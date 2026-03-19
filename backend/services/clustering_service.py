from typing import List


class ClusteringService:
    """Grid-based clustering of geo-coordinates with zoom-aware precision."""

    # Zoom level to geohash decimal precision mapping
    # Lower precision = bigger grid cells = more aggregation
    ZOOM_PRECISION = {
        # zoom_level: decimal_places
        # 1 decimal ~11km, 2 decimal ~1.1km, 3 decimal ~110m, 4 decimal ~11m
        range(0, 8): 1,      # country/state view
        range(8, 12): 2,     # city/neighborhood view
        range(12, 16): 3,    # street view
        range(16, 22): 4,    # building view
    }

    @staticmethod
    def _precision_for_zoom(zoom: int | None, radius_km: float) -> int:
        """Determine grid precision from zoom level or radius."""
        if zoom is not None:
            for zoom_range, precision in ClusteringService.ZOOM_PRECISION.items():
                if zoom in zoom_range:
                    return precision
            return 3  # default

        # Fallback: derive from radius
        if radius_km > 20:
            return 1
        if radius_km > 5:
            return 2
        return 3

    @staticmethod
    def cluster(
        points: list[tuple[str, float, float]],
        radius_km: float,
        zoom: int | None = None,
    ) -> List[dict]:
        """
        Cluster points by rounding to a grid.
        :param points: list of (member_id, longitude, latitude)
        :param radius_km: search radius — fallback for grid precision
        :param zoom: optional map zoom level for adaptive precision
        :return: list of cluster dicts with centroid + count
        """
        precision = ClusteringService._precision_for_zoom(zoom, radius_km)

        clusters: dict[tuple[float, float], dict] = {}

        for _member, r_lon, r_lat in points:
            grid_lat = round(r_lat, precision)
            grid_lon = round(r_lon, precision)
            key = (grid_lat, grid_lon)

            if key not in clusters:
                clusters[key] = {"count": 0, "lat_sum": 0.0, "lon_sum": 0.0}

            clusters[key]["count"] += 1
            clusters[key]["lat_sum"] += r_lat
            clusters[key]["lon_sum"] += r_lon

        results = []
        for key, data in clusters.items():
            count = data["count"]
            results.append({
                "geohash": f"{key[0]},{key[1]}",
                "latitude": data["lat_sum"] / count,
                "longitude": data["lon_sum"] / count,
                "count": count,
            })

        return results
