from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceResult:
    transmitted: float
    scattered: float
    absorbed: float
    warnings: tuple[str, ...]


def calculate_airless_surface() -> SurfaceResult:
    """Return the documented neutral-surface educational partition.

    The catalog intentionally has no scientific albedo field, so this is one
    shared model assumption rather than a body-specific invented value.
    """
    return SurfaceResult(
        transmitted=0.85,
        scattered=0.10,
        absorbed=0.05,
        warnings=(
            "No scientific surface albedo is stored; the generic airless surface partition was used.",
        ),
    )
