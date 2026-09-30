from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModeledLightColor:
    label: str
    rgb: tuple[int, int, int]
    spectral_band: str | None
    confidence: str
    basis: str


NEUTRAL_LIGHT = ModeledLightColor(
    label="neutral",
    rgb=(244, 232, 190),
    spectral_band="broad-visible",
    confidence="fallback",
    basis="neutral-fallback",
)


TRANSMITTED_COLORS = {
    "white": (244, 244, 238),
    "yellow": (255, 214, 107),
    "orange": (245, 154, 74),
    "red": (239, 107, 92),
    "blue": (116, 167, 255),
    "pale blue": (169, 220, 232),
    "pale yellow": (244, 230, 163),
    "dim white": (174, 184, 197),
    "gray-white": (196, 200, 202),
}


def derive_scattered_light_color(
    has_atmosphere: bool,
    composition: dict[str, float],
) -> ModeledLightColor:
    """Return a conservative broad visible-light class, never a perceived-color claim."""
    if not has_atmosphere or sum(composition.values()) <= 0:
        return NEUTRAL_LIGHT

    methane = composition.get("CH4", 0.0)
    nitrogen = composition.get("N2", 0.0)
    hydrogen_helium = composition.get("H2", 0.0) + composition.get("He", 0.0)

    # NASA documents orange aerosol haze from N2/CH4 photochemistry on Titan.
    if nitrogen >= 0.75 and methane >= 0.005:
        return ModeledLightColor(
            label="orange",
            rgb=(232, 158, 76),
            spectral_band=None,
            confidence="supported",
            basis="nitrogen-methane-photochemical-haze",
        )

    # Methane removes red light in H2/He atmospheres, leaving a cyan appearance.
    if hydrogen_helium >= 0.5 and methane >= 0.01:
        return ModeledLightColor(
            label="cyan",
            rgb=(137, 205, 218),
            spectral_band="blue-green-visible",
            confidence="supported",
            basis="methane-red-absorption",
        )

    # The aggregate model has gases but no aerosol/cloud inputs. Its defensible
    # spectral statement is the short-visible preference of molecular scattering.
    return ModeledLightColor(
        label="blue",
        rgb=(132, 180, 242),
        spectral_band="short-visible",
        confidence="modeled",
        basis="molecular-rayleigh-scattering",
    )


def derive_transmitted_light_color(dominant_color: str) -> ModeledLightColor:
    rgb = TRANSMITTED_COLORS.get(dominant_color)
    if rgb is None:
        return NEUTRAL_LIGHT
    return ModeledLightColor(
        label=dominant_color,
        rgb=rgb,
        spectral_band="broad-visible",
        confidence="modeled",
        basis="existing-dominant-light-classification",
    )
