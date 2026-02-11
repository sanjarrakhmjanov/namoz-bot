from __future__ import annotations

from math import atan2, cos, degrees, radians, sin


KAABA_LAT = 21.4225
KAABA_LON = 39.8262


def qibla_bearing(lat: float, lon: float) -> float:
    lat_rad = radians(lat)
    lon_rad = radians(lon)
    kaaba_lat = radians(KAABA_LAT)
    kaaba_lon = radians(KAABA_LON)

    d_lon = kaaba_lon - lon_rad
    x = sin(d_lon) * cos(kaaba_lat)
    y = cos(lat_rad) * sin(kaaba_lat) - sin(lat_rad) * cos(kaaba_lat) * cos(d_lon)
    bearing = (degrees(atan2(x, y)) + 360.0) % 360.0
    return bearing


def bearing_to_compass(bearing: float) -> str:
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    index = int((bearing + 11.25) // 22.5) % 16
    return directions[index]
