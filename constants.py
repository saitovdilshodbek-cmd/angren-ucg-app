"""
UCG Platform — Global Constants
================================

Barcha magic numbers va constants bitta joyda.
Endi `MIN_PATENT_MONTE_CARLO = 10000` kabi tushunarsiz qiymatlar
constanta sifatida documentatsiya bilan keladi.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math


# ── Numerical Tolerances ───────────────────────────────────────────────
class Numerical:
    """Numerical computation tolerances."""
    EPS_GENERAL: float = 1e-12       # General numerical tolerance (near-zero guard)
    EPS_SPARSE: float = 1e-6         # Sparse matrix threshold
    EPS_MESH: float = 1e-9           # Mesh Jacobian determinant floor (regularization)
    PI: float = math.pi
    DEG2RAD: float = math.pi / 180.0


# ── FEM Solver Constants ───────────────────────────────────────────────
class FEMConstants:
    """FEM solver configuration constants.

    References:
        - Hughes (2000). The Finite Element Method.
        - Brenner & Scott (2008). Mathematical Theory of FEM.
    """
    MAX_ITERATIONS: int = 1000         # Maximum solver iterations
    MIN_MESH_QUALITY: float = 0.3      # Minimum element quality (Jacobian ratio)
    MIN_ELEMENT_SIZE: float = 0.01     # Minimum element edge length (m)
    MAX_ELEMENT_SIZE: float = 100.0    # Maximum element edge length (m)
    GAUSS_POINTS_LINEAR: int = 2       # Gauss quadrature points for linear elements
    EXPECTED_CONVERGENCE_ORDER_LINEAR: float = 1.0  # O(h) for linear hexahedral
    GCI_SAFETY_FACTOR: float = 1.25    # Grid Convergence Index safety (Roache 1994)
    GCI_THRESHOLD: float = 0.05        # GCI must be < 5% for convergence

    # Material property bounds (linear elasticity)
    YOUNGS_MODULUS_MIN: float = 1.0       # Pa (minimum physically meaningful)
    YOUNGS_MODULUS_MAX: float = 1e12      # Pa (diamond ~ 1e12)
    POISSON_RATIO_MIN: float = -1.0       # Auxetic materials
    POISSON_RATIO_MAX: float = 0.5        # Incompressible limit (with EPS regularization)


# ── Monte Carlo Constants ──────────────────────────────────────────────
class MonteCarloConstants:
    """Monte Carlo simulation constants.

    Justification for sample sizes:
        - 10,000: Gelman-Rubin R-hat < 1.1 (Kass et al., 1998)
        - 50,000: 95% CI half-width < 1% of std (CLT)
        - 500,000: RAM limit on 8GB machine (8 bytes/sample)
    """
    MIN_SAMPLES: int = 10_000          # Minimum for R-hat convergence
    DEFAULT_SAMPLES: int = 50_000      # Default for 95% CI
    MAX_SAMPLES: int = 500_000         # RAM-limited (8GB machine)
    CONVERGENCE_TOLERANCE: float = 0.01  # 1% accuracy
    BURN_IN_DEFAULT: int = 1_000       # Burn-in samples to discard
    GEWEKE_THRESHOLD: float = 2.0      # |z| < 2 for convergence
    GELMAN_RUBIN_THRESHOLD: float = 1.01  # R-hat < 1.01


# ── Patent Constants ───────────────────────────────────────────────────
class PatentConstants:
    """Patent analysis constants."""
    MIN_CLAIMS: int = 1
    MAX_CLAIMS: int = 100              # EPO/USPTO practical limit
    MIN_NOVELTY_SCORE: float = 0.5     # Below 50% = weak novelty
    PRIOR_ART_MIN_RECORDS: int = 100   # Minimum for credible novelty assessment
    AHP_CONSISTENCY_THRESHOLD: float = 0.10  # Saaty's CR threshold
    ISO_7064_BASE: int = 11            # ISO 7064 MOD 11-2 for DOI check digit


# ── Security Constants ─────────────────────────────────────────────────
class SecurityConstants:
    """Security and cryptography constants."""
    RSA_KEY_SIZE: int = 4096           # RSA-4096 (NIST SP 800-57 Level 1+)
    RSA_PUBLIC_EXPONENT: int = 65537   # Standard Fermat prime F4
    PBKDF2_ITERATIONS: int = 100_000   # OWASP recommendation (2023)
    SALT_LENGTH_BYTES: int = 16        # 128-bit salt
    KEY_FILE_PERMISSION: int = 0o600   # rw------- (private key)
    KEY_DIR_PERMISSION: int = 0o700    # rwx------ (key directory)
    PUBLIC_KEY_PERMISSION: int = 0o644 # rw-r--r-- (public key)


# ── API Client Constants ───────────────────────────────────────────────
class APIConstants:
    """External API client constants."""
    DEFAULT_TIMEOUT_SEC: float = 20.0
    MAX_RETRIES: int = 3
    BACKOFF_BASE_SEC: float = 2.0      # Exponential backoff: 2^n seconds
    RATE_LIMIT_STATUS: int = 429
    USER_AGENT: str = "UCG-Patent-Platform/6.0 (mailto:research@example.com)"


# ── Path Constants ─────────────────────────────────────────────────────
class PathConstants:
    """Filesystem path constants (all Path objects, not str)."""
    HOME: Path = Path.home()
    UCG_ROOT: Path = HOME / ".ucg_platform"
    LOG_DIR: Path = UCG_ROOT / "logs"
    KEY_DIR: Path = UCG_ROOT / "keys"
    REPORT_DIR: Path = UCG_ROOT / "reports"
    DB_DIR: Path = UCG_ROOT / "db"

    # Default file paths
    PRIVATE_KEY_PATH: Path = KEY_DIR / "ucg_patent_private.pem"
    PUBLIC_KEY_PATH: Path = KEY_DIR / "ucg_patent_public.pem"
    KEY_FINGERPRINT_PATH: Path = KEY_DIR / "key_fingerprint.json"
    AUDIT_DB_PATH: Path = DB_DIR / "audit_merkle_chain.db"
    EXPERIMENTAL_DB_PATH: Path = DB_DIR / "experimental_database.db"
    PRIOR_ART_DB_PATH: Path = DB_DIR / "prior_art_database.db"

    # Log file
    LOG_FILE: Path = LOG_DIR / "ucg_platform.log"


# ── Streamlit Constants ────────────────────────────────────────────────
class StreamlitConstants:
    """Streamlit UI constants."""
    MAX_CACHE_ENTRIES: int = 32        # Streamlit cache limit
    CACHE_VERSION: int = 3             # Bump when cache structure changes


# ── Subprocess Allowlist ───────────────────────────────────────────────
class SubprocessConstants:
    """Allowed subprocess commands (security: explicit allowlist)."""
    SAFE_COMMANDS: tuple = (
        ("git", "rev-parse", "--short", "HEAD"),  # Get git commit hash
        # Add more safe commands here as needed
    )
    MAX_TIMEOUT_SEC: float = 5.0       # Maximum subprocess timeout


__all__ = [
    "Numerical", "FEMConstants", "MonteCarloConstants", "PatentConstants",
    "SecurityConstants", "APIConstants", "PathConstants", "StreamlitConstants",
    "SubprocessConstants",
]
