# Scenario Mode

Scenario Mode is request-local and never mutates the scientific catalog. It accepts atmosphere presence, pressure, density, and the supported gas fractions.

One submission recalculates:

- the original visible-light energy partition and color;
- ML eligibility, ensemble uncertainty, OOD screening, and physics fallback;
- atmospheric shielding category;
- combined magnetic-plus-atmospheric shielding; and
- qualitative scenario-adjusted surface particle exposure.

Magnetic family, field geometry, and reference radiation context are not user-editable and do not change when the atmosphere changes. This keeps hypothetical atmosphere experiments separate from unsupported magnetic inventions.
