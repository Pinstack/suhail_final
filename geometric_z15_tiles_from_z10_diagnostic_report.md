# Geometric Pipeline Diagnostic Report: Download Errors, Autotuning, and Retries

## 1. **Retry Logic in Tile Downloader**
- The downloader (`AsyncTileDownloader.fetch_tile`) implements retries for each tile download using the following logic:
  - For each tile, it attempts up to `settings.retry_config.max_attempts` (default: 3).
  - On `aiohttp.ClientError`, it logs a warning and retries with exponential backoff (`await asyncio.sleep(2**attempt)`).
  - If all attempts fail, it logs an error and skips the tile.
  - 404s are not retried; they are logged and skipped immediately.

## 2. **Semaphore and Concurrency Control**
- The downloader uses an `asyncio.Semaphore` to limit concurrent downloads, with the limit set by `settings.max_concurrent_downloads` (default: 20, autotuned).
- Earlier versions imposed a 30s timeout when acquiring the semaphore. With hundreds of thousands of queued tasks, this led to mass "Timeout acquiring semaphore" errors. The timeout has been removed and `download_many` processes tiles in batches to prevent starvation.

## 3. **Autotuning Feedback Loop**
- The `PipelineAutotuner` adjusts concurrency and batch sizes based on throughput and error counts.
- However, in the main pipeline, the call to `autotuner.record_download` always passes `errors=0`:
  ```python
  autotuner.record_download(len(tiles), elapsed_dl, errors=0)  # TODO: count actual errors
  ```
- This means the autotuner is **not aware of download failures** (404s, timeouts, or other errors) and cannot react to them.

## 4. **Error Counting and Reporting**
- The downloader logs warnings and errors for failed downloads, but does not return or aggregate error counts to the orchestrator.
- As a result, the pipeline's error rate is underreported, and the autotuner cannot decrease concurrency in response to high error rates or timeouts.

## 5. **Timeouts and Retries**
- Timeouts in `fetch_tile` are handled by retrying (up to max attempts), but if all attempts fail, the tile is skipped.
- Persistent timeouts (e.g., due to server overload) are not surfaced to the autotuner.

## 6. **Recommendations**
- **Aggregate and return error counts** from `download_many` to the orchestrator, so the autotuner can react to real error rates.
- **Pass the actual error count** to `autotuner.record_download`.
- Optionally, **log a summary of error types** (404s, timeouts, connection errors) for better diagnostics.
- Consider **reducing initial concurrency** or making it more conservative if timeouts are frequent.

## 7. **Summary Table**
| Aspect                | Current State         | Issue/Gap                | Recommendation                |
|-----------------------|----------------------|--------------------------|-------------------------------|
| Retry logic           | Implemented          | Works as intended        | No change needed              |
| Concurrency control   | Autotuned, semaphore | Not error-aware          | Pass error count to autotuner |
| Error aggregation     | Not implemented      | Errors not surfaced      | Aggregate/return error count  |
| Timeout handling      | Retries, then skip   | Not reported to autotune | Aggregate/report timeouts     |
| 404 handling          | Logged, skipped      | Not reported to autotune | Optionally aggregate          |

---

**Actionable next step:**
- Refactor `download_many` and the orchestrator to count and report download errors, so the autotuner can dynamically adjust concurrency in response to real-world error rates. 