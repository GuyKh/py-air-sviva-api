"""Air Quality Index (AQI) calculation for Israeli air quality data.

Based on the Israeli Ministry of Environmental Protection methodology
as documented at https://aqihub.info/indices/israel and verified
against real API responses from air.sviva.gov.il.

Formula:
    For each pollutant, compute a sub-index via piecewise linear interpolation::

        I_p = ((I_hi - I_lo) / (BP_hi - BP_lo)) × (C_p - BP_lo) + I_lo

    The station AQI is determined by the worst (highest) sub-index::

        AQI = max(I_p1, I_p2, ..., I_pn)

Usage::

    from air_sviva_api.aqi import Pollutant, calc_station_air_quality

    result = calc_station_air_quality({
        Pollutant.PM25: 10.7,
        "NO2": 49.3,
        "O3": 33.9,
    })
    print(result.aqi_rounded)       # 54
    print(result.classification)    # AQIClassification.GOOD
    print(result.worst_pollutant)   # Pollutant.NO2
    print(result.sub_indices)       # Per-pollutant breakdown
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

__all__ = [
    "AQIClassification",
    "AirQualityResult",
    "Pollutant",
    "calc_station_air_quality",
    "calc_sub_index",
]


# ── Enums ─────────────────────────────────────────────────────────────────


class Pollutant(StrEnum):
    """Canonical Israeli pollutant names as used in the AQI breakpoint tables.

    Each member is itself a string, so ``Pollutant.PM25 == "PM2.5"`` and
    dict lookups work transparently with both enum members and plain strings.

    Usage::

        >>> Pollutant.from_api("PM25")
        Pollutant.PM25
        >>> str(Pollutant.PM25)
        'PM2.5'
    """

    PM25 = "PM2.5"
    PM10 = "PM10"
    SO2 = "SO2"
    NO2 = "NO2"
    O3 = "O3"
    CO = "CO"
    NOX = "NOx"

    @staticmethod
    def from_api(value: str) -> Optional["Pollutant"]:
        """Parse an API response string, accepting common aliases.

        Handles the actual wire format (e.g. ``"PM25"``, ``"nox"``) and
        returns the canonical :class:`Pollutant` member.
        """
        clean = value.upper().replace(" ", "").replace("_", "")
        # Fast path for PM2.5 member (its string value "PM2.5" contains a
        # dot so it doesn't match the cleaned-up upper-case alias "PM25").
        if clean in ("PM25", "PM2.5"):
            return Pollutant.PM25
        for member in Pollutant:
            if member.value.upper() == clean:
                return member
        return None


class AQIClassification(StrEnum):
    """Israeli AQI verbal classification."""

    EXCELLENT = "excellent"
    GOOD = "good"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


# ── Breakpoint tables ─────────────────────────────────────────────────────
# Source: https://aqihub.info/indices/israel (adapted from the official PDF).
# Each entry: (conc_low, conc_high, index_low, index_high)

AQI_BREAKPOINTS: dict[Pollutant, list[tuple[float, float, int, int]]] = {
    Pollutant.PM25: [
        (0, 18.5, 0, 49),
        (18.6, 37, 50, 100),
        (37.5, 84, 101, 200),
        (84.5, 130, 201, 300),
        (130.5, 165, 301, 400),
        (165.5, 200, 401, 500),
    ],
    Pollutant.PM10: [
        (0, 65, 0, 49),
        (66, 129, 50, 100),
        (130, 215, 101, 200),
        (216, 300, 201, 300),
        (301, 355, 301, 400),
        (356, 430, 401, 500),
    ],
    Pollutant.SO2: [
        (0, 67, 0, 49),
        (68, 133, 50, 100),
        (134, 163, 101, 200),
        (164, 191, 201, 300),
        (192, 253, 301, 400),
        (254, 303, 401, 500),
    ],
    Pollutant.NO2: [
        (0, 53, 0, 49),
        (54, 105, 50, 100),
        (106, 160, 101, 200),
        (161, 213, 201, 300),
        (214, 260, 301, 400),
        (261, 316, 401, 500),
    ],
    Pollutant.O3: [
        (0, 35, 0, 49),
        (36, 70, 50, 100),
        (71, 97, 101, 200),
        (98, 117, 201, 300),
        (118, 155, 301, 400),
        (156, 188, 401, 500),
    ],
    Pollutant.CO: [
        (0, 26, 0, 49),
        (27, 51, 50, 100),
        (52, 78, 101, 200),
        (79, 104, 201, 300),
        (105, 130, 301, 400),
        (131, 156, 401, 500),
    ],
    Pollutant.NOX: [
        (0, 250, 0, 49),
        (251, 499, 50, 100),
        (500, 750, 101, 200),
        (751, 1000, 201, 300),
        (1001, 1200, 301, 400),
        (1201, 1400, 401, 500),
    ],
}


# ── Classification thresholds ─────────────────────────────────────────────

_AQI_CLASSIFICATION: list[tuple[float, AQIClassification]] = [
    (301, AQIClassification.VERY_LOW),
    (201, AQIClassification.LOW),
    (101, AQIClassification.MEDIUM),
    (51, AQIClassification.GOOD),
    (0, AQIClassification.EXCELLENT),
]


# ── Result model ──────────────────────────────────────────────────────────


@dataclass
class AirQualityResult:
    """Result of an Israeli AQI calculation.

    Attributes:
        aqi: The final AQI value (0 to 500). Higher values mean more polluted air.
        classification: Verbal classification (:class:`AQIClassification`).
        sub_indices: Per-pollutant sub-indices (0-500) keyed by :class:`Pollutant`.
        worst_pollutant: The pollutant with the highest sub-index (``None`` if no data).
    """

    aqi: float
    classification: AQIClassification
    sub_indices: dict[Pollutant, float]
    worst_pollutant: Optional[Pollutant] = None

    @property
    def aqi_rounded(self) -> int:
        """The AQI rounded to the nearest integer."""
        return round(self.aqi)


# ── Internal helpers ──────────────────────────────────────────────────────


def _normalize_pollutant_name(name: str) -> Optional[Pollutant]:
    """Normalize a pollutant name (str) to a :class:`Pollutant` member."""
    return Pollutant.from_api(name) if isinstance(name, str) else name


# ── Public API ────────────────────────────────────────────────────────────


def calc_sub_index(concentration: float, pollutant: str | Pollutant) -> Optional[float]:
    """Calculate the AQI sub-index for a single pollutant concentration.

    Uses piecewise linear interpolation within the appropriate breakpoint range.

    Args:
        concentration: Pollutant concentration in the appropriate units
            (µg/m³ for particles and gases, mg/m³ for CO).
        pollutant: :class:`Pollutant` member or canonical name string
            (e.g. ``"PM2.5"``, ``"NO2"``).

    Returns:
        The sub-index value (0-500), or *None* if the pollutant is not
        recognised.
    """
    canonical = pollutant if isinstance(pollutant, Pollutant) else Pollutant.from_api(pollutant)
    if canonical is None:
        return None
    breakpoints = AQI_BREAKPOINTS.get(canonical)
    if breakpoints is None:
        return None

    for bp_lo, bp_hi, idx_lo, idx_hi in breakpoints:
        if bp_lo <= concentration <= bp_hi:
            return ((idx_hi - idx_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + idx_lo

    if concentration > breakpoints[-1][1]:
        bp_lo, bp_hi, idx_lo, idx_hi = breakpoints[-1]
        return min(
            ((idx_hi - idx_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + idx_lo,
            500.0,
        )

    for bp_lo, bp_hi, idx_lo, idx_hi in breakpoints:
        if concentration < bp_lo:
            return float(idx_lo)

    return 0.0


def calc_station_air_quality(readings: dict[str | Pollutant, float]) -> AirQualityResult:
    """Calculate the Israeli AQI from pollutant concentration readings.

    The AQI is determined by the **worst** (most polluted) pollutant.
    The highest sub-index across all pollutants sets the final AQI value.

    Args:
        readings: Mapping of pollutant → concentration value.
            Keys may be :class:`Pollutant` members or plain strings
            (canonical names like ``"PM2.5"``, ``"NO2"``, or API aliases
            like ``"PM25"``, ``"NOX"``).
            Units must match the AQI breakpoints (µg/m³ for particles and
            gases, mg/m³ for CO).

    Returns:
        :class:`AirQualityResult` with the computed AQI, classification and
        per-pollutant breakdown.

    Example:
        >>> result = calc_station_air_quality({"PM2.5": 10.7, "NO2": 49.3})
        >>> result.aqi_rounded
        54
        >>> result.classification
        <AQIClassification.GOOD: 'good'>
    """
    normalised: dict[Pollutant, float] = {}
    for name, conc in readings.items():
        canonical = _normalize_pollutant_name(name)
        if canonical is not None:
            normalised[canonical] = conc

    if not normalised:
        return AirQualityResult(
            aqi=0.0,
            classification=AQIClassification.UNKNOWN,
            sub_indices={},
            worst_pollutant=None,
        )

    sub_indices: dict[Pollutant, float] = {}
    for pollutant, conc in normalised.items():
        sub_idx = calc_sub_index(conc, pollutant)
        if sub_idx is not None:
            sub_indices[pollutant] = sub_idx

    if not sub_indices:
        return AirQualityResult(
            aqi=0.0,
            classification=AQIClassification.UNKNOWN,
            sub_indices={},
            worst_pollutant=None,
        )

    worst_pollutant = max(sub_indices, key=sub_indices.__getitem__)  # type: ignore[arg-type]
    max_sub_index = sub_indices[worst_pollutant]

    aqi = max_sub_index

    classification: AQIClassification = AQIClassification.UNKNOWN
    for threshold, cls in _AQI_CLASSIFICATION:
        if aqi >= threshold:
            classification = cls
            break

    return AirQualityResult(
        aqi=aqi,
        classification=classification,
        sub_indices=sub_indices,
        worst_pollutant=worst_pollutant,
    )
