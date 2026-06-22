"""
Unit tests for System Integrity Monitor.

Tests cover:
  - Health check functions (database, RSA, blockchain, etc.)
  - File hash calculation (SHA-256)
  - Dynamic patent readiness score
  - Citation generator
  - Authors info
  - Git commit retrieval

Run: pytest tests/test_system_monitor.py -v
"""

import unittest
import os
import tempfile
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHealthChecks(unittest.TestCase):
    """Test health check functions."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_check_database(self):
        """Database check should return 'Connected' or 'Failed'."""
        result = self.monitor.check_database()
        self.assertIn(result, ["Connected", "Failed"])

    def test_check_rsa_status(self):
        """RSA check should return 'Active' or 'Missing Keys'."""
        result = self.monitor.check_rsa_status()
        self.assertIn(result, ["Active", "Missing Keys"])

    def test_check_blockchain_status(self):
        """Blockchain check should return 'Active' or 'Not Initialized'."""
        result = self.monitor.check_blockchain_status()
        self.assertIn(result, ["Active", "Not Initialized"])

    def test_check_patent_engine(self):
        """Patent engine check should return a string."""
        result = self.monitor.check_patent_engine()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_check_fem_solver(self):
        """FEM solver check should return a string."""
        result = self.monitor.check_fem_solver()
        self.assertIsInstance(result, str)

    def test_check_ai_module(self):
        """AI module check should return a string."""
        result = self.monitor.check_ai_module()
        self.assertIsInstance(result, str)

    def test_check_doi_engine(self):
        """DOI engine check should return a string."""
        result = self.monitor.check_doi_engine()
        self.assertIsInstance(result, str)

    def test_check_prior_art(self):
        """Prior art check should return a string."""
        result = self.monitor.check_prior_art()
        self.assertIsInstance(result, str)

    def test_check_validation(self):
        """Validation check should return a string."""
        result = self.monitor.check_validation()
        self.assertIsInstance(result, str)

    def test_check_reproducibility(self):
        """Reproducibility check should return a string."""
        result = self.monitor.check_reproducibility()
        self.assertIsInstance(result, str)


class TestFileHash(unittest.TestCase):
    """Test file hash calculation."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_hash_existing_file(self):
        """Hash of existing file should return 64-char hex string."""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            f.flush()
            path = f.name
        try:
            h = self.monitor.calculate_file_hash(path)
            self.assertEqual(len(h), 64)  # SHA-256 hex
            self.assertTrue(all(c in "0123456789abcdef" for c in h))
        finally:
            os.unlink(path)

    def test_hash_nonexistent_file(self):
        """Hash of non-existent file should return 'FILE_NOT_FOUND'."""
        h = self.monitor.calculate_file_hash("/nonexistent/path/file.txt")
        self.assertEqual(h, "FILE_NOT_FOUND")

    def test_hash_consistency(self):
        """Same file content should produce same hash."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("consistent content")
            f.flush()
            path = f.name
        try:
            h1 = self.monitor.calculate_file_hash(path)
            h2 = self.monitor.calculate_file_hash(path)
            self.assertEqual(h1, h2)
        finally:
            os.unlink(path)


class TestPatentReadiness(unittest.TestCase):
    """Test dynamic patent readiness score."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_readiness_score_in_range(self):
        """Score should be between 0 and 100."""
        result = self.monitor.compute_patent_readiness()
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_readiness_has_grade(self):
        """Result should include a grade."""
        result = self.monitor.compute_patent_readiness()
        self.assertIn("grade", result)
        self.assertIsInstance(result["grade"], str)

    def test_readiness_has_breakdown(self):
        """Result should include breakdown dict."""
        result = self.monitor.compute_patent_readiness()
        self.assertIn("breakdown", result)
        self.assertIsInstance(result["breakdown"], dict)
        self.assertGreater(len(result["breakdown"]), 5)

    def test_readiness_has_recommendation(self):
        """Result should include a recommendation."""
        result = self.monitor.compute_patent_readiness()
        self.assertIn("recommendation", result)
        self.assertIsInstance(result["recommendation"], str)

    def test_readiness_max_score(self):
        """Max score should be 100."""
        result = self.monitor.compute_patent_readiness()
        self.assertEqual(result["max_score"], 100)


class TestCitation(unittest.TestCase):
    """Test citation info."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_citation_info_exists(self):
        """CITATION_INFO should have required fields."""
        info = self.monitor.CITATION_INFO
        self.assertIn("title", info)
        self.assertIn("version", info)
        self.assertIn("year", info)
        self.assertIn("doi", info)
        self.assertIn("url", info)

    def test_citation_version_is_6(self):
        """Citation version should be 6.0.0."""
        self.assertEqual(self.monitor.CITATION_INFO["version"], "6.0.0")


class TestAuthors(unittest.TestCase):
    """Test authors info."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_authors_not_empty(self):
        """AUTHORS list should not be empty."""
        self.assertGreater(len(self.monitor.AUTHORS), 0)

    def test_author_has_required_fields(self):
        """Each author should have name, role, affiliation."""
        author = self.monitor.AUTHORS[0]
        self.assertIn("name", author)
        self.assertIn("role", author)
        self.assertIn("affiliation", author)
        self.assertIn("email", author)


class TestGitCommit(unittest.TestCase):
    """Test git commit retrieval."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_git_commit_returns_string(self):
        """get_git_commit should return a string."""
        result = self.monitor.get_git_commit()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_git_commit_n_a_on_failure(self):
        """If git not available, should return 'N/A'."""
        # This test just verifies the function doesn't crash
        result = self.monitor.get_git_commit()
        # Either a commit hash or 'N/A'
        self.assertTrue(result == "N/A" or len(result) >= 4)


class TestSelfTests(unittest.TestCase):
    """Test the self-test function."""

    def setUp(self):
        import _system_monitor as monitor
        self.monitor = monitor

    def test_run_self_tests(self):
        """run_self_tests should return a dict with results."""
        result = self.monitor.run_self_tests()
        self.assertIn("version", result)
        self.assertIn("tests", result)
        self.assertIn("all_passed", result)
        self.assertIsInstance(result["tests"], dict)


if __name__ == "__main__":
    unittest.main()
