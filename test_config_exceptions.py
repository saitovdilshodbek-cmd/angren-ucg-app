"""
Unit tests for Configuration, Exceptions, and Version modules.

Tests cover:
  - Config validation (invalid values raise ConfigurationError)
  - Environment variable loading (DB_PASSWORD, DATACITE_PREFIX, etc.)
  - Exception hierarchy
  - Version info

Run: pytest tests/test_config_exceptions.py -v
"""

import os
import unittest
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig(unittest.TestCase):
    """Test configuration management."""

    def test_default_config_validates(self) -> None:
        """Default config should pass validation."""
        from config import Config
        config = Config()
        # Should not raise
        config.validate()

    def test_fem_invalid_tolerance_raises(self) -> None:
        """Invalid FEM tolerance should raise ConfigurationError."""
        from config import FEMConfig
        from exceptions import ConfigurationError
        config = FEMConfig(tolerance=-1.0)
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_fem_invalid_quality_raises(self) -> None:
        """Invalid min_element_quality should raise ConfigurationError."""
        from config import FEMConfig
        from exceptions import ConfigurationError
        config = FEMConfig(min_element_quality=2.0)  # > 1.0
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_patent_invalid_novelty_raises(self) -> None:
        """Invalid min_novelty_score should raise ConfigurationError."""
        from config import PatentConfig
        from exceptions import ConfigurationError
        config = PatentConfig(min_novelty_score=1.5)  # > 1.0
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_security_invalid_rsa_key_size(self) -> None:
        """Invalid RSA key size should raise ConfigurationError."""
        from config import SecurityConfig
        from exceptions import ConfigurationError
        config = SecurityConfig(rsa_key_size=1234)  # not in (2048, 3072, 4096, 8192)
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_database_postgres_requires_password(self) -> None:
        """PostgreSQL backend requires DB_PASSWORD env var."""
        from config import DatabaseConfig
        from exceptions import ConfigurationError
        # Ensure DB_PASSWORD is not set
        old_val = os.environ.pop("DB_PASSWORD", None)
        try:
            config = DatabaseConfig(backend="postgres")
            with self.assertRaises(ConfigurationError) as ctx:
                config.validate()
            self.assertIn("DB_PASSWORD", str(ctx.exception))
        finally:
            if old_val is not None:
                os.environ["DB_PASSWORD"] = old_val

    def test_database_sqlite_no_password_required(self) -> None:
        """SQLite backend does NOT require DB_PASSWORD."""
        from config import DatabaseConfig
        # Ensure DB_PASSWORD is not set
        old_val = os.environ.pop("DB_PASSWORD", None)
        try:
            config = DatabaseConfig(backend="sqlite")
            config.validate()  # Should not raise
        finally:
            if old_val is not None:
                os.environ["DB_PASSWORD"] = old_val

    def test_config_to_dict_no_secrets_by_default(self) -> None:
        """to_dict() should NOT include secret values by default."""
        from config import Config
        config = Config()
        d = config.to_dict()
        # Check that password value is not in dict (only 'db_password_set' boolean)
        self.assertNotIn("db_password", d["database"])
        self.assertIn("db_password_set", d["database"])

    def test_ensure_directories_creates_paths(self) -> None:
        """ensure_directories() should create required paths."""
        from config import Config
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config = Config()
            config.log_dir = tmp / "logs"
            config.report_dir = tmp / "reports"
            config.security.key_dir = tmp / "keys"
            config.ensure_directories()
            self.assertTrue(config.log_dir.exists())
            self.assertTrue(config.report_dir.exists())
            self.assertTrue(config.security.key_dir.exists())

    def test_monte_carlo_min_samples(self) -> None:
        """MIN_SAMPLES < 1000 should raise."""
        from config import MonteCarloConfig
        from exceptions import ConfigurationError
        config = MonteCarloConfig(MIN_SAMPLES=100)
        with self.assertRaises(ConfigurationError):
            config.validate()


class TestExceptions(unittest.TestCase):
    """Test custom exception hierarchy."""

    def test_base_exception(self) -> None:
        """UCGException should be catchable as Exception."""
        from exceptions import UCGException
        with self.assertRaises(Exception):
            raise UCGException("test")

    def test_fem_mesh_error_is_fem_solver_error(self) -> None:
        """FEMMeshError should be catchable as FEMSolverError (inheritance)."""
        from exceptions import FEMSolverError, FEMMeshError
        with self.assertRaises(FEMSolverError):
            raise FEMMeshError("bad mesh")

    def test_patent_search_error_is_patent_analysis(self) -> None:
        """PatentSearchError should be catchable as PatentAnalysisError."""
        from exceptions import PatentAnalysisError, PatentSearchError
        with self.assertRaises(PatentAnalysisError):
            raise PatentSearchError("search failed")

    def test_api_error_has_status_code(self) -> None:
        """APIError should preserve status_code and endpoint."""
        from exceptions import APIError
        try:
            raise APIError("rate limited", status_code=429, endpoint="https://api.example.com")
        except APIError as e:
            self.assertEqual(e.status_code, 429)
            self.assertEqual(e.endpoint, "https://api.example.com")
            self.assertIn("429", str(e))
            self.assertIn("api.example.com", str(e))

    def test_security_error_hierarchy(self) -> None:
        """KeyManagementError should be catchable as SecurityError."""
        from exceptions import SecurityError, KeyManagementError
        with self.assertRaises(SecurityError):
            raise KeyManagementError("key not found")

    def test_exception_with_detail(self) -> None:
        """UCGException should support optional detail."""
        from exceptions import UCGException
        e = UCGException("main message", detail="extra context")
        self.assertIn("main message", str(e))
        self.assertIn("extra context", str(e))


class TestVersion(unittest.TestCase):
    """Test version management."""

    def test_version_string_format(self) -> None:
        """Version should follow semantic versioning."""
        from version import __version__
        # Format: X.Y.Z or X.Y.Z-prerelease
        import re
        pattern = r"^\d+\.\d+\.\d+(-[\w-]+)?$"
        self.assertRegex(__version__, pattern,
                         f"Version '{__version__}' doesn't match semver pattern")

    def test_version_info_dict(self) -> None:
        """get_version_info() should return complete dict."""
        from version import get_version_info
        info = get_version_info()
        self.assertIn("version", info)
        self.assertIn("build", info)
        self.assertIn("author", info)
        self.assertIn("license", info)
        self.assertIn("components", info)

    def test_version_is_v6(self) -> None:
        """Version should be 6.0.0 or higher."""
        from version import version_info
        self.assertGreaterEqual(version_info.major, 6,
                                f"Expected major version >= 6, got {version_info.major}")


class TestLogger(unittest.TestCase):
    """Test structured logging setup."""

    def test_setup_logging_creates_directory(self) -> None:
        """setup_logging() should create log directory."""
        from logger import setup_logging
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = setup_logging(log_dir=tmpdir, level="DEBUG")
            self.assertTrue(log_dir.exists())
            self.assertTrue(log_dir.is_dir())

    def test_get_logger_returns_logger(self) -> None:
        """get_logger() should return a Logger instance."""
        from logger import get_logger
        import logging
        logger = get_logger("test_module")
        self.assertIsInstance(logger, logging.Logger)

    def test_get_logger_namespaced(self) -> None:
        """get_logger() should namespace under ucg_platform."""
        from logger import get_logger
        logger = get_logger("test_module")
        self.assertTrue(logger.name.startswith("ucg_platform"))


if __name__ == "__main__":
    unittest.main()
