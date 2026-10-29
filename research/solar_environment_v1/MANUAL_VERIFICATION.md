# Manual UI verification — 2026-10-30

The local production UI was inspected in the in-app Chromium browser against the live FastAPI development service.

Verified selected-body profiles:

- Earth — intrinsic dipole, supported evidence, separate photon/particle streams, substantial combined shielding.
- Mercury — intrinsic dipole.
- Venus — induced draped-field profile, not an Earth-like dipole.
- Mars — crustal-remnant profile. A 1 MPa atmosphere scenario changed atmospheric shielding from limited to substantial and surface exposure from high to low without changing the magnetic family.
- Jupiter — intrinsic dipole, extreme magnetic/radiation context, no solid-surface exposure claim.
- Saturn — aligned intrinsic family.
- Uranus and Neptune — tilted/offset family.
- Pluto — unknown family with limited-evidence badge and no invented 3D global-field overlay.

The catalog/API and component tests additionally cover Moon, Titan, Ganymede, Io, Europa, and Callisto special cases. The 32-body prediction sweep returned 32 matching environment records. Browser inspection found one nullable Scenario Mode input warning; the form normalization was fixed and the warning did not recur after reload. The remaining Three.js Clock deprecation warning originates in the current React Three Fiber dependency rather than this environment expansion.
