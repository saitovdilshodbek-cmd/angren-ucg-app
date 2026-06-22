"""
Application configuration with environment-based secrets.

Bu modul credentials larni .env fayldan o'qiydi (hardcoded emas).
Dataclass-based config bilan type-safe va validated.

Usage:
    from config import Config, get_config
    config = Config()
    config.validate()
    db_pass = config.db_password  # .env dan o'qiladi
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from exceptions import ConfigurationError


# ── FEM solver configuration ───────────────────────────────────────────────
@dataclass
class FEMConfig:
    """FEM solver configuration."""
    max_iterations: int = 1000
    tolerance: float = 1e-6
    min_element_quality: float = 0.3
    solver_type: str = "direct"  # 'direct' | 'iterative'
    use_sparse: bool = True

    def validate(self) -> None:
        """Validate FEM configuration."""
        if self.max_iterations <= 0:
            raise ConfigurationError(f"max_iterations must be > 0: {self.max_iterations}")
        if self.tolerance <= 0:
            raise ConfigurationError(f"tolerance must be > 0: {self.tolerance}")
        if not 0.0 <= self.min_element_quality <= 1.0:
            raise ConfigurationError(
                f"min_element_quality must be in [0, 1]: {self.min_element_quality}"
            )
        if self.solver_type not in ("direct", "iterative"):
            raise ConfigurationError(f"Unknown solver_type: {self.solver_type}")


# ── Patent analysis configuration ──────────────────────────────────────────
@dataclass
class PatentConfig:
    """Patent analysis configuration."""
    min_novelty_score: float = 0.5
    max_claims: int = 100
    enable_ai_search: bool = True
    prior_art_db_path: Path = field(default_factory=lambda: Path("prior_art_database.db"))

    def validate(self) -> None:
        """Validate patent configuration."""
        if not 0.0 <= self.min_novelty_score <= 1.0:
            raise ConfigurationError(
                f"min_novelty_score must be in [0, 1]: {self.min_novelty_score}"
            )
        if self.max_claims <= 0:
            raise ConfigurationError(f"max_claims must be > 0: {self.max_claims}")


# ── Security configuration ─────────────────────────────────────────────────
@dataclass
class SecurityConfig:
    """Security configuration (RSA, PQC, audit)."""
    rsa_key_size: int = 4096
    enable_audit_chain: bool = True
    enable_post_quantum: bool = False  # Future: enable CRYSTALS-Kyber
    key_dir: Path = field(default_factory=lambda: Path.home() / ".ucg_platform" / "keys")
    key_password_env: str = "UCG_KEY_PASSWORD"  # env var name (not the password itself)

    def validate(self) -> None:
        """Validate security configuration."""
        if self.rsa_key_size not in (2048, 3072, 4096, 8192):
            raise ConfigurationError(
                f"rsa_key_size must be 2048/3072/4096/8192: {self.rsa_key_size}"
            )


# ── Database configuration ─────────────────────────────────────────────────
@dataclass
class DatabaseConfig:
    """Database configuration (PostgreSQL / SQLite)."""
    backend: str = "sqlite"  # 'sqlite' | 'postgres'
    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ucg_platform"
    db_user: str = "ucg_user"
    # Password is read from env var, NEVER hardcoded
    db_password_env: str = "DB_PASSWORD"
    # SQLite
    sqlite_path: Path = field(default_factory=lambda: Path.home() / ".ucg_platform" / "ucg.db")

    @property
    def db_password(self) -> Optional[str]:
        """Read DB password from environment variable."""
        return os.getenv(self.db_password_env)

    def validate(self) -> None:
        """Validate database configuration."""
        if self.backend not in ("sqlite", "postgres"):
            raise ConfigurationError(f"Unknown backend: {self.backend}")
        if self.backend == "postgres":
            if not self.db_password:
                raise ConfigurationError(
                    f"PostgreSQL backend requires {self.db_password_env} env var. "
                    "Set it in .env file (never commit to git)."
                )

    def get_connection_string(self) -> str:
        """Build connection string (PostgreSQL only)."""
        if self.backend != "postgres":
            raise ConfigurationError("Connection string only for PostgreSQL backend")
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# ── Monte Carlo configuration ──────────────────────────────────────────────
@dataclass
class MonteCarloConfig:
    """Monte Carlo simulation configuration.

    These values are based on statistical theory:
      - MIN_SAMPLES = 10000: Gelman-Rubin R-hat < 1.1 uchun kerak
      - DEFAULT_SAMPLES = 50000: 95% CI 1% accuracy uchun
      - MAX_SAMPLES = 500000: 8GB RAM cheklovi
    """
    MIN_SAMPLES: int = 10000
    DEFAULT_SAMPLES: int = 50000
    MAX_SAMPLES: int = 500000
    CONVERGENCE_TOLERANCE: float = 0.01  # 1% accuracy
    BURN_IN_FRACTION: float = 0.02  # 2% burn-in

    def validate(self) -> None:
        if self.MIN_SAMPLES < 1000:
            raise ConfigurationError("MIN_SAMPLES must be >= 1000")
        if self.MAX_SAMPLES < self.MIN_SAMPLES:
            raise ConfigurationError("MAX_SAMPLES must be >= MIN_SAMPLES")


# ── API credentials configuration ──────────────────────────────────────────
@dataclass
class APICredentialsConfig:
    """External API credentials (all from env vars, NEVER hardcoded).

    All credentials are read from environment variables.
    The .env file (which is .gitignored) contains the actual values.
    """
    # DataCite DOI registration
    datacite_prefix: Optional[str] = field(default_factory=lambda: os.getenv("DATACITE_PREFIX"))
    datacite_api_token: Optional[str] = field(default_factory=lambda: os.getenv("DATACITE_API_TOKEN"))
    datacite_username: Optional[str] = field(default_factory=lambda: os.getenv("DATACITE_USERNAME"))
    datacite_password: Optional[str] = field(default_factory=lambda: os.getenv("DATACITE_PASSWORD"))

    # Espacenet OPS (OAuth 2.0)
    eps_ops_key: Optional[str] = field(default_factory=lambda: os.getenv("EPS_OPS_KEY"))
    eps_ops_secret: Optional[str] = field(default_factory=lambda: os.getenv("EPS_OPS_SECRET"))

    # Crossref (polite pool — just email)
    crossref_mailto: str = field(default_factory=lambda: os.getenv("CROSSREF_MAILTO", "research@example.com"))

    # IPFS (optional)
    ipfs_api_url: str = field(default_factory=lambda: os.getenv("IPFS_API_URL", "http://127.0.0.1:5001/api/v0"))

    def validate(self) -> None:
        """Validate API credentials (warnings only, not errors)."""
        import warnings
        if not self.datacite_prefix:
            warnings.warn(
                "DATACITE_PREFIX not set. DOI registration disabled. "
                "Set it in .env file (see .env.example)."
            )
        if not (self.eps_ops_key and self.eps_ops_secret):
            warnings.warn(
                "EPS_OPS_KEY/EPS_OPS_SECRET not set. Espacenet API disabled. "
                "Get credentials at https://www.epo.org/registering-registering/registering.html"
            )


# ── Main configuration ─────────────────────────────────────────────────────
@dataclass
class Config:
    """Main application configuration.

    All secrets come from environment variables (via .env file).
    NEVER hardcode credentials in source code.

    Usage:
        config = Config()
        config.validate()
        # Access sub-configs
        config.fem.max_iterations
        config.security.rsa_key_size
        config.database.db_password  # from env
    """
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "False").lower() == "true")
    log_dir: Path = field(default_factory=lambda: Path(
        os.getenv("LOG_DIR", str(Path.home() / ".ucg_platform" / "logs"))
    ).expanduser())
    report_dir: Path = field(default_factory=lambda: Path(
        os.getenv("REPORT_DIR", str(Path.home() / ".ucg_platform" / "reports"))
    ).expanduser())

    # Sub-configurations
    fem: FEMConfig = field(default_factory=FEMConfig)
    patent: PatentConfig = field(default_factory=PatentConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    monte_carlo: MonteCarloConfig = field(default_factory=MonteCarloConfig)
    api_credentials: APICredentialsConfig = field(default_factory=APICredentialsConfig)

    def validate(self) -> None:
        """Validate all sub-configurations."""
        # Validate log_dir
        if self.log_dir.exists() and not self.log_dir.is_dir():
            raise ConfigurationError(f"log_dir must be a directory: {self.log_dir}")
        # Validate report_dir
        if self.report_dir.exists() and not self.report_dir.is_dir():
            raise ConfigurationError(f"report_dir must be a directory: {self.report_dir}")
        # Validate sub-configs
        self.fem.validate()
        self.patent.validate()
        self.security.validate()
        self.database.validate()
        self.monte_carlo.validate()
        self.api_credentials.validate()

    def ensure_directories(self) -> None:
        """Create required directories with proper permissions."""
        self.log_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        self.report_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        self.security.key_dir.mkdir(parents=True, exist_ok=True, mode=0o700)  # stricter for keys
        if self.database.backend == "sqlite":
            self.database.sqlite_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

    def to_dict(self, include_secrets: bool = False) -> dict:
        """Convert config to dict (for logging/debugging).

        Args:
            include_secrets: If True, include secret values (DANGEROUS — use only for debug).
        """
        result = {
            "debug": self.debug,
            "log_dir": str(self.log_dir),
            "report_dir": str(self.report_dir),
            "fem": {
                "max_iterations": self.fem.max_iterations,
                "tolerance": self.fem.tolerance,
                "min_element_quality": self.fem.min_element_quality,
                "solver_type": self.fem.solver_type,
            },
            "patent": {
                "min_novelty_score": self.patent.min_novelty_score,
                "max_claims": self.patent.max_claims,
                "enable_ai_search": self.patent.enable_ai_search,
            },
            "security": {
                "rsa_key_size": self.security.rsa_key_size,
                "enable_audit_chain": self.security.enable_audit_chain,
                "enable_post_quantum": self.security.enable_post_quantum,
                "key_dir": str(self.security.key_dir),
            },
            "database": {
                "backend": self.database.backend,
                "db_host": self.database.db_host,
                "db_port": self.database.db_port,
                "db_name": self.database.db_name,
                "db_user": self.database.db_user,
                "db_password_set": bool(self.database.db_password),
            },
            "monte_carlo": {
                "MIN_SAMPLES": self.monte_carlo.MIN_SAMPLES,
                "DEFAULT_SAMPLES": self.monte_carlo.DEFAULT_SAMPLES,
                "MAX_SAMPLES": self.monte_carlo.MAX_SAMPLES,
            },
            "api_credentials": {
                "datacite_prefix_set": bool(self.api_credentials.datacite_prefix),
                "datacite_token_set": bool(self.api_credentials.datacite_api_token),
                "eps_ops_set": bool(self.api_credentials.eps_ops_key),
                "crossref_mailto": self.api_credentials.crossref_mailto,
            },
        }
        if include_secrets and self.debug:
            import warnings
            warnings.warn("Including secrets in config dump — DEBUG mode only!")
            result["api_credentials"]["datacite_prefix"] = self.api_credentials.datacite_prefix
        return result


# ── Singleton config instance ──────────────────────────────────────────────
_config_instance: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get singleton config instance.

    Args:
        reload: If True, re-read environment variables.

    Returns:
        Validated Config instance.
    """
    global _config_instance
    if _config_instance is None or reload:
        # Load .env file if available
        if DOTENV_AVAILABLE:
            env_path = Path.cwd() / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        _config_instance = Config()
        _config_instance.validate()
    return _config_instance


def reset_config() -> None:
    """Reset singleton (mainly for testing)."""
    global _config_instance
    _config_instance = None
