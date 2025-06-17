"""Lightweight Mapbox Vector Tile decoder.

Focus: fast feature counting / basic attribute extraction, not coordinate reprojection.
"""
from __future__ import annotations

from typing import Dict, List, Any, Sequence

import mapbox_vector_tile


class MVTDecoder:
    """Decode raw Mapbox Vector Tile bytes.

    For analysis scripts we only need feature counts, so we simply return the
    features list per layer with properties preserved; geometry remains raw.
    """

    def decode_bytes(
        self, tile_data: bytes, layers: Sequence[str] | None = None
    ) -> Dict[str, List[dict[str, Any]]]:
        """Decode tile data.

        Parameters
        ----------
        tile_data : bytes
            Raw .pbf data.
        layers : list[str] | None
            If provided, only these layers are returned.
        Returns
        -------
        dict[str, list[dict]]
            Mapping of layer name to list of feature dicts.
        """
        decoded = mapbox_vector_tile.decode(tile_data)
        if layers is not None:
            decoded = {k: v for k, v in decoded.items() if k in layers}
        return decoded 