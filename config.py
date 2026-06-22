"""
UCG Platform — Configuration Management
========================================

Type-safe, dataclass-based configuration with validation.
Endi hardcoded values yo'q — barcha konfiguratsiya shu yerda.

Usage:
    from ucg_platform.config import Config

    config = Config()
    config.validate()  # Raises ConfigurationError agar noto'g'ri bo'lsa

    if config.debug:
        print(f"Log dir: {config.log_dir}")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .exceptions import ConfigurationError
from .constants import (
    FEMConstants, MonteCarloConstants, PatentConstants,
    SecurityConstants, APIConstants, PathConstants, StreamlitConstants,
)


def _env_bool(name: str, default: bool = False) -> bool:
    """Read boolean from environment variable."""
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


def _env_int(name: str, default: int) -> int:
    """Read integer from environment variable."""
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        raise ConfigurationError(f"Env var {name} must be integer, got: {val}")


def _env_float(name: str, default: float) -> float:
    """Read float from environment variable."""
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        raise ConfigurationError(f"Env var {name} must be float, got: {val}")


def _env_path(name: str, default: Path) -> Path:
    """Read Path from environment variable (expands ~)."""
    val = os.getenv(name)
    if val is None:
        return default
    return Path(val).expanduser()


@dataclass
class FEMConfig:
    """FEM solver configuration."""
    max_iterations: int = FEMConstants.MAX_ITERATIONS
    tolerance: float = 1e-6
    min_element_quality: float = FEMConstants.MIN_MESH_QUALITY
    min_element_size: float = FEMConstants.MIN_ELEMENT_SIZE
    max_element_size: float = FEMConstants.MAX_ELEMENT_SIZE
    solver_type: str = "direct"  # 'direct' | 'iterative'

    def validate(self) -> None:
        if self.tolerance <= 0:
            raise ConfigurationError(f"FEM tolerance must be > 0: {self.tolerance}")
        if self.max_iterations <= 0:
            raise ConfigurationError(f"max_iterations must be > 0: {self.max_iterations}")
        if not 0 <= self.min_element_quality <= 1:
            raise ConfigurationError(
                f"min_element_quality must be in [0, 1]: {self.min_element_quality}"
            )
        if self.solver_type not in ("direct", "iterative"):
            raise ConfigurationError(
                f"solver_type must be 'direct' or 'iterative': {self.solver_type}"
            )


@dataclass
class MonteCarloConfig:
    """Monte Carlo simulation configuration."""
    min_samples: int = MonteCarloConstants.MIN_SAMPLES
    default_samples: int = MonteCarloConstants.DEFAULT_SAMPLES
    max_samples: int = MonteCarloConstants.MAX_SAMPLES
    convergence_tolerance: float = MonteCarloConstants.CONVERGENCE_TOLERANCE
    burn_in: int = MonteCarloConstants.BURN_IN_DEFAULT

    def validate(self) -> None:
        if self.min_samples < 1000:
            raise ConfigurationError(f"min_samples too low: {self.min_samples}")
        if self.default_samples < self.min_samples:
            raise ConfigurationError("default_samples < min_samples")
        if self.max_samples < self.default_samples:
            raise ConfigurationError("max_samples < default_samples")


@dataclass
class PatentConfig:
    """Patent analysis configuration."""
    min_novelty_score: float = PatentConstants.MIN_NOVELTY_SCORE
    max_claims: int = PatentConstants.MAX_CLAIMS
    enable_ai_search: bool = True
    ahp_consistency_threshold: float = PatentConstants.AHP_CONSISTENCY_THRESHOLD

    def validate(self) -> None:
        if not 0 < self.min_novelty_score < 1:
            raise ConfigurationError(
                f"min_novelty_score must be in (0, 1): {self.min_novelty_score}"
            )
        if self.max_claims <= 0 or self.max_claims > 200:
            raise ConfigurationError(f"max_claims out of range: {self.max_claims}")


@dataclass
class SecurityConfig:
    """Security configuration."""
    rsa_key_size: int = SecurityConstants.RSA_KEY_SIZE
    enable_audit_chain: bool = True
    enable_ipfs: bool = False
    enable_post_quantum: bool = False
    key_dir: Path = PathConstants.KEY_DIR
    private_key_path: Path = PathConstants.PRIVATE_KEY_PATH
    public_key_path: Path = PathConstants.PUBLIC_KEY_PATH

    def validate(self) -> None:
        if self.rsa_key_size not in (2048, 3072, 4096, 8192):
            raise ConfigurationError(
                f"rsa_key_size must be 2048/3072/4096/8192: {self.rsa_key_size}"
            )


@dataclass
class APIConfig:
    """External API configuration (credentials from env vars)."""
    datacite_prefix: Optional[str] = field(default_factory=lambda: os.getenv("DATACITE_PREFIX"))
    datacite_api_token: Optional[str] = field(default_factory=lambda: os.getenv("DATACITE_API_TOKEN"))
    eps_ops_key: Optional[str] = field(default_factory=lambda: os.getenv("EPS_OPS_KEY"))
    eps_ops_secret: Optional[str] = field(default_factory=lambda: os.getenv("EPS_OPS_SECRET"))
    crossref_mailto: str = field(default_factory=lambda: os.getenv("CROSSREF_MAILTO", "research@example.com"))
    timeout_sec: float = APIConstants.DEFAULT_TIMEOUT_SEC
    max_retries: int = APIConstants.MAX_RETRIES

    def validate(self) -> None:
        if self.timeout_sec <= 0:
            raise ConfigurationError(f"timeout_sec must be > 0: {self.timeout_sec}")
        if self.max_retries <= 0:
            raise ConfigurationError(f"max_retries must be > 0: {self.max_retries}")

    def has_datacite_credentials(self) -> bool:
        """Check if DataCite credentials are configured."""
        return bool(self.datacite_prefix and self.datacite_api_token)

    def has_espacenet_credentials(self) -> bool:
        """Check if Espacenet OPS credentials are configured."""
        return bool(self.eps_ops_key and self.eps_ops_secret)


@dataclass
class DatabaseConfig:
    """Database configuration (PostgreSQL/SQLite)."""
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: _env_int("DB_PORT", 5432))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "ucg_platform"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "ucg_user"))
    db_password: Optional[str] = field(default_factory=lambda: os.getenv("DB_PASSWORD"))
    use_postgres: bool = field(default_factory=lambda: _env_bool("USE_POSTGRES", False))
    sqlite_path: Path = PathConstants.AUDIT_DB_PATH

    def validate(self) -> None:
        if self.use_postgres and not self.db_password:
            raise ConfigurationError(
                "DB_PASSWORD environment variable required when USE_POSTGRES=True. "
                "Set it in .env file (never commit to git)."
            )
        if not 0 < self.db_port < 65536:
            raise ConfigurationError(f"db_port out of range: {self.db_port}")


@dataclass
class Config:
    """Main application configuration.

    Usage:
        config = Config()
        config.validate()

        if config.debug:
            print(f"Log dir: {config.log_dir}")

        # Access sub-configs
        fem_settings = config.fem
        patent_settings = config.patent
    """
    # Top-level
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", False))
    log_dir: Path = field(default_factory=lambda: _env_path("LOG_DIR", PathConstants.LOG_DIR))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Sub-configurations
    fem: FEMConfig = field(default_factory=FEMConfig)
    monte_carlo: MonteCarloConfig = field(default_factory=MonteCarloConfig)
    patent: PatentConfig = field(default_factory=PatentConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    api: APIConfig = field(default_factory=APIConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    def validate(self) -> None:
        """Validate entire configuration. Raises ConfigurationError on failure."""
        # Log dir check
        if self.log_dir.exists() and not self.log_dir.is_dir():
            raise ConfigurationError(f"log_dir must be a directory: {self.log_dir}")

        # Log level check
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ConfigurationError(
                f"log_level must be one of {valid_levels}: {self.log_level}"
            )

        # Validate sub-configs
        self.fem.validate()
        self.monte_carlo.validate()
        self.patent.validate()
        self.security.validate()
        self.api.validate()
        self.database.validate()

    def ensure_directories(self) -> None:
        """Create required directories with proper permissions."""
        for path in [
            PathConstants.UCG_ROOT,
            self.log_dir,
            PathConstants.KEY_DIR,
            PathConstants.REPORT_DIR,
            PathConstants.DB_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)
            # Key dir gets restrictive permissions
            if path == PathConstants.KEY_DIR:
                path.chmod(SecurityConstants.KEY_DIR_PERMISSION)


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get singleton Config instance (validated)."""
    global _config
    if _config is None:
        _config = Config()
        _config.validate()
    return _config


__all__ = [
    "Config", "FEMConfig", "MonteCarloConfig", "PatentConfig",
    "SecurityConfig", "APIConfig", "DatabaseConfig",
    "get_config",
]
