import aiohttp
import asyncio
from typing import List, Dict, Any

from meshic_pipeline.config import settings
from meshic_pipeline.exceptions import (
    ExternalAPIException,
    with_retry,
    RetryConfig,
    async_error_context,
)
from meshic_pipeline.logging_utils import get_logger, log_performance
from meshic_pipeline.persistence.models import (
    Transaction,
    BuildingRule,
    ParcelPriceMetric,
)
from datetime import datetime

logger = get_logger(__name__)


class SuhailAPIClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests, including authentication if configured."""
        headers = {"Content-Type": "application/json"}
        if settings.api_config.api_key:
            headers["Authorization"] = f"Bearer {settings.api_config.api_key}"
            # or use: headers["X-API-Key"] = settings.api_config.api_key
        return headers

    @with_retry(
        RetryConfig(
            max_attempts=settings.retry_config.max_attempts,
            base_delay=settings.retry_config.base_delay,
            retriable_exceptions=(ExternalAPIException, aiohttp.ClientResponseError),
        )
    )
    @log_performance("fetch_transactions")
    async def fetch_transactions(self, parcel_objectid: str) -> List[Transaction]:
        """Fetches and parses transaction data for a single parcel with retries."""
        url = f"{settings.api_config.transactions_url}?parcelObjectId={parcel_objectid}"

        async with async_error_context(
            "fetch_transactions",
            "enrichment.api",
            user_data={"parcel_objectid": parcel_objectid, "url": url},
        ) as ctx:
            try:
                timeout = aiohttp.ClientTimeout(total=settings.api_config.timeout)
                headers = self._get_headers()
                async with self.session.get(url, headers=headers, timeout=timeout) as response:
                    if 400 <= response.status < 500:
                        logger.warning(
                            f"Client error {response.status} for {url}",
                            context={
                                "parcel_objectid": parcel_objectid,
                                "status": response.status,
                            },
                        )
                        return []

                    if response.status >= 500:
                        raise ExternalAPIException(
                            f"Server error {response.status} from transactions API",
                            context=ctx,
                            cause=aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                            ),
                        )

                    response.raise_for_status()

                    data = await response.json()
                    if (
                        not data
                        or not data.get("status")
                        or "data" not in data
                        or not data["data"].get("transactions")
                    ):
                        logger.debug(f"No transactions found for parcel {parcel_objectid}")
                        return []

                    new_transactions = []
                    for tx_data in data["data"]["transactions"]:
                        transaction_date = None
                        if tx_data.get("transactionDate"):
                            try:
                                transaction_date = datetime.fromisoformat(
                                    tx_data.get("transactionDate").replace("Z", "+00:00")
                                )
                            except ValueError as e:
                                logger.warning(
                                    f"Failed to parse transaction_date: {tx_data.get('transactionDate')}",
                                    context={
                                        "parcel_objectid": parcel_objectid,
                                        "error": str(e),
                                    },
                                )

                        new_tx = Transaction(
                            transaction_id=tx_data.get("transactionNumber"),
                            parcel_objectid=parcel_objectid,
                            transaction_price=tx_data.get("transactionPrice"),
                            price_of_meter=tx_data.get("priceOfMeter"),
                            transaction_date=transaction_date,
                            area=tx_data.get("area"),
                            raw_data=tx_data,
                        )
                        new_transactions.append(new_tx)

                    logger.debug(
                        f"Fetched {len(new_transactions)} transactions for parcel {parcel_objectid}",
                        context={
                            "parcel_objectid": parcel_objectid,
                            "transaction_count": len(new_transactions),
                        },
                    )
                    return new_transactions

            except aiohttp.ClientError as e:
                raise ExternalAPIException(
                    f"Network error fetching transactions for {parcel_objectid}",
                    context=ctx,
                    cause=e,
                )
            except Exception as e:
                logger.error(
                    f"Error processing transaction data for {parcel_objectid}: {e}",
                    context={"parcel_objectid": parcel_objectid, "error": str(e)},
                )
                return []

    async def fetch_building_rules(self, parcel_objectid: str) -> List[BuildingRule]:
        """Fetches and parses building rules for a single parcel with retries."""
        url = f"{settings.api_config.building_rules_url}?parcelObjectId={parcel_objectid}"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                async with self.session.get(url, headers=headers) as response:
                    if response.status >= 500:
                        response.raise_for_status()

                    if 400 <= response.status < 500:
                        logger.warning(
                            f"Client error {response.status} for {url}. Not retrying."
                        )
                        return []

                    response.raise_for_status()

                    data = await response.json()
                    if (
                        not data
                        or not data.get("status")
                        or "data" not in data
                        or not data["data"]
                    ):
                        return []

                    rules = []
                    for rule_data in data["data"]:
                        new_rule = BuildingRule(
                            parcel_objectid=parcel_objectid,
                            building_rule_id=rule_data.get("id"),
                            zoning_id=rule_data.get("zoningId"),
                            zoning_color=rule_data.get("zoningColor"),
                            zoning_group=rule_data.get("zoningGroup"),
                            landuse=rule_data.get("landuse"),
                            description=rule_data.get("description"),
                            name=rule_data.get("name"),
                            coloring=rule_data.get("coloring"),
                            coloring_description=rule_data.get(
                                "coloringDescription"
                            ),
                            max_building_coefficient=rule_data.get(
                                "maxBuildingCoefficient"
                            ),
                            max_building_height=rule_data.get("maxBuildingHeight"),
                            max_parcel_coverage=rule_data.get("maxParcelCoverage"),
                            max_rule_depth=rule_data.get("maxRuleDepth"),
                            main_streets_setback=rule_data.get(
                                "mainStreetsSetback"
                            ),
                            secondary_streets_setback=rule_data.get(
                                "secondaryStreetsSetback"
                            ),
                            side_rear_setback=rule_data.get("sideRearSetback"),
                            raw_data=rule_data,
                        )
                        rules.append(new_rule)
                    return rules

            except aiohttp.ClientError as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {url} with error: {e}"
                )
                if attempt + 1 == max_retries:
                    logger.error(f"All retries failed for {url}")
                    return []
                await asyncio.sleep(1)  # simple backoff
        return []

    async def fetch_price_metrics(
        self, parcel_objectids: List[str]
    ) -> List[ParcelPriceMetric]:
        """Fetches and parses price metrics for a list of parcels."""
        url = settings.api_config.price_metrics_url
        max_retries = 3
        params = [("parcelObjsIds", pid) for pid in parcel_objectids]
        params.append(("groupingType", "Monthly"))

        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status >= 500:
                        response.raise_for_status()

                    if 400 <= response.status < 500:
                        logger.warning(
                            f"Client error {response.status} for {url}. Not retrying."
                        )
                        return []

                    response.raise_for_status()

                    data = await response.json()
                    if not data or not data.get("status") or "data" not in data:
                        return []

                    metrics = []
                    for parcel_data in data["data"]:
                        pid = parcel_data.get("parcelObjId")
                        for metric_data in parcel_data.get("parcelMetrics", []):
                            new_metric = ParcelPriceMetric(
                                parcel_objectid=pid,
                                month=metric_data.get("month"),
                                year=metric_data.get("year"),
                                metrics_type=metric_data.get("metricsType"),
                                average_price_of_meter=metric_data.get(
                                    "avaragePriceOfMeter"
                                ),
                            )
                            metrics.append(new_metric)
                    return metrics

            except aiohttp.ClientError as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {url} with error: {e}"
                )
                if attempt + 1 == max_retries:
                    logger.error(f"All retries failed for {url}")
                    return []
                await asyncio.sleep(1)
        return []