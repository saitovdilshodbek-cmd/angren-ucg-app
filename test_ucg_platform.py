"""
Unit tests for ucg_platform package.
Run: pytest tests/ -v --cov=ucg_platform
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ucg_platform.exceptions import (
    FEMMeshError, FEMMaterialError, ValidationError,
    ConfigurationError, KeyManagementError,
)
from ucg_platform.version import __version__, get_version_info
from ucg_platform.constants import (
    Numerical, FEMConstants, MonteCarloConstants, SecurityConstants,
)
from ucg_platform.config import Config, FEMConfig, get_config
from ucg_platform.logger import setup_logging, get_logger


class TestVersion(unittest.TestCase):
    """Test version management."""

    def test_version_format(self):
        """Version should follow semver format."""
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")

    def test_version_info(self):
        """get_version_info should return dict with required keys."""
        info = get_version_info()
        self.assertIn("version", info)
        self.assertIn("build", info)
        self.assertIn("extensions", info)
        self.assertEqual(info["version"], __version__)


class TestConstants(unittest.TestCase):
    """Test constants are properly defined."""

    def test_numerical_constants(self):
        """Numerical constants should be positive floats."""
        self.assertGreater(Numerical.EPS_GENERAL, 0)
        self.assertGreater(Numerical.EPS_SPARSE, Numerical.EPS_GENERAL)
        self.assertAlmostEqual(Numerical.PI, 3.14159265, places=7)

    def test_fem_constants(self):
        """FEM constants should be in valid ranges."""
        self.assertGreater(FEMConstants.MAX_ITERATIONS, 0)
        self.assertGreater(FEMConstants.MIN_MESH_QUALITY, 0)
        self.assertLess(FEMConstants.MIN_MESH_QUALITY, 1)
        self.assertGreater(FEMConstants.POISSON_RATIO_MAX, FEMConstants.POISSON_RATIO_MIN)

    def test_monte_carlo_constants(self):
        """MC constants should be consistent."""
        self.assertGreater(MonteCarloConstants.DEFAULT_SAMPLES, MonteCarloConstants.MIN_SAMPLES)
        self.assertGreater(MonteCarloConstants.MAX_SAMPLES, MonteCarloConstants.DEFAULT_SAMPLES)


class TestConfig(unittest.TestCase):
    """Test configuration management."""

    def test_default_config_validates(self):
        """Default config should validate without errors."""
        config = Config()
        config.validate()

    def test_invalid_fem_tolerance(self):
        """FEM tolerance <= 0 should raise ConfigurationError."""
        config = Config()
        config.fem.tolerance = -1.0
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_invalid_patent_novelty(self):
        """Patent novelty out of (0, 1) should raise ConfigurationError."""
        config = Config()
        config.patent.min_novelty_score = 1.5
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_invalid_solver_type(self):
        """Invalid solver_type should raise ConfigurationError."""
        config = Config()
        config.fem.solver_type = "invalid"
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_invalid_log_level(self):
        """Invalid log level should raise ConfigurationError."""
        config = Config()
        config.log_level = "VERBOSE"
        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_singleton_config(self):
        """get_config should return same instance."""
        c1 = get_config()
        c2 = get_config()
        self.assertIs(c1, c2)


class TestExceptions(unittest.TestCase):
    """Test custom exception hierarchy."""

    def test_exception_hierarchy(self):
        """All custom exceptions should inherit from UCGException."""
        from ucg_platform.exceptions import UCGException
        for exc_class in [FEMMeshError, FEMMaterialError, ValidationError,
                          ConfigurationError, KeyManagementError]:
            self.assertTrue(issubclass(exc_class, UCGException))

    def test_fem_exception_hierarchy(self):
        """FEM exceptions should inherit from FEMSolverError."""
        from ucg_platform.exceptions import FEMSolverError
        self.assertTrue(issubclass(FEMMeshError, FEMSolverError))
        self.assertTrue(issubclass(FEMMaterialError, FEMSolverError))

    def test_exception_messages(self):
        """Exception messages should be preserved."""
        msg = "Test error message"
        exc = FEMMeshError(msg)
        self.assertEqual(str(exc), msg)


class TestLogger(unittest.TestCase):
    """Test logging setup."""

    def test_setup_logging(self):
        """setup_logging should not raise with valid args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=Path(tmpdir), level="DEBUG")
            logger = get_logger("test")
            logger.info("Test log message")

    def test_invalid_log_level(self):
        """Invalid level should raise ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            setup_logging(level="INVALID_LEVEL")


class TestFEMMaterialValidation(unittest.TestCase):
    """Test FEM material property validation."""

    def test_valid_material(self):
        """Valid E and nu should not raise."""
        E = 200e9  # 200 GPa (steel)
        nu = 0.3
        self.assertGreater(E, FEMConstants.YOUNGS_MODULUS_MIN)
        self.assertLess(E, FEMConstants.YOUNGS_MODULUS_MAX)
        self.assertGreater(nu, FEMConstants.POISSON_RATIO_MIN)
        self.assertLess(nu, FEMConstants.POISSON_RATIO_MAX)

    def test_negative_youngs_modulus(self):
        """Negative E should be invalid."""
        E = -100.0
        self.assertLess(E, FEMConstants.YOUNGS_MODULUS_MIN)

    def test_poisson_ratio_out_of_range(self):
        """nu > 0.5 should be invalid (physical limit)."""
        nu = 0.6
        self.assertGreater(nu, FEMConstants.POISSON_RATIO_MAX)

    def test_incompressible_limit(self):
        """nu = 0.5 (incompressible) should be at boundary (allowed with EPS)."""
        nu = 0.5
        self.assertAlmostEqual(nu, FEMConstants.POISSON_RATIO_MAX)


if __name__ == "__main__":
    unittest.main()
