"""
Unit tests for UCG SCI-Grade Platform — FEM Solver.

Tests cover:
  - Stiffness matrix shape and symmetry
  - SPD (symmetric positive definite) property
  - Invalid material property handling (E, nu)
  - Degenerate element (Jacobian ≈ 0) handling
  - Near-incompressible material (nu → 0.5)

Run: pytest tests/test_fem_solver.py -v
"""

import unittest
import numpy as np
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFEMStiffness(unittest.TestCase):
    """Test FEM element stiffness matrix computation."""

    def setUp(self) -> None:
        """Setup: standard 1×1×1 cube element."""
        self.nodes_cube = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        self.E_standard = 200e3  # 200 GPa (steel)
        self.nu_standard = 0.3   # typical rock

    def test_stiffness_matrix_shape(self) -> None:
        """Stiffness matrix must be 24×24 (8 nodes × 3 DOF)."""
        from app import element_stiffness_3d
        Ke = element_stiffness_3d(self.nodes_cube, self.E_standard, self.nu_standard)
        self.assertEqual(Ke.shape, (24, 24),
                         f"Expected (24, 24), got {Ke.shape}")

    def test_stiffness_symmetry(self) -> None:
        """Stiffness matrix must be symmetric (K = K^T)."""
        from app import element_stiffness_3d
        Ke = element_stiffness_3d(self.nodes_cube, self.E_standard, self.nu_standard)
        np.testing.assert_array_almost_equal(
            Ke, Ke.T, decimal=6,
            err_msg="Stiffness matrix not symmetric"
        )

    def test_stiffness_all_finite(self) -> None:
        """All entries must be finite (no NaN, no Inf)."""
        from app import element_stiffness_3d
        Ke = element_stiffness_3d(self.nodes_cube, self.E_standard, self.nu_standard)
        self.assertTrue(np.all(np.isfinite(Ke)),
                        "Stiffness matrix contains NaN or Inf")

    def test_stiffness_spd_property(self) -> None:
        """Stiffness matrix should be positive semi-definite (eigenvalues >= 0)."""
        from app import element_stiffness_3d
        Ke = element_stiffness_3d(self.nodes_cube, self.E_standard, self.nu_standard)
        eigs = np.linalg.eigvalsh(Ke)
        # Allow small numerical error
        self.assertGreaterEqual(eigs.min(), -1e-6,
                                f"Min eigenvalue {eigs.min()} < 0 (not PSD)")

    def test_invalid_E_negative(self) -> None:
        """Negative Young's modulus should raise FEMMaterialError."""
        from app import element_stiffness_3d
        from exceptions import FEMMaterialError
        with self.assertRaises(FEMMaterialError):
            element_stiffness_3d(self.nodes_cube, E=-100, nu=0.3)

    def test_zero_E_raises(self) -> None:
        """E = 0 should raise FEMMaterialError (must be > 0)."""
        from app import element_stiffness_3d
        from exceptions import FEMMaterialError
        with self.assertRaises(FEMMaterialError):
            element_stiffness_3d(self.nodes_cube, E=0.0, nu=0.3)

    def test_invalid_nu_above_05_raises(self) -> None:
        """nu > 0.5 should raise FEMMaterialError (must be ≤ 0.5)."""
        from app import element_stiffness_3d
        from exceptions import FEMMaterialError
        with self.assertRaises(FEMMaterialError):
            element_stiffness_3d(self.nodes_cube, self.E_standard, nu=0.6)

    def test_incompressible_limit_nu_05(self) -> None:
        """nu = 0.5 (incompressible) must work with EPS_GENERAL."""
        from app import element_stiffness_3d
        Ke = element_stiffness_3d(self.nodes_cube, self.E_standard, nu=0.5)
        self.assertTrue(np.all(np.isfinite(Ke)),
                        "Incompressible limit (nu=0.5) failed — EPS_GENERAL needed")

    def test_near_incompressible_nu_0499(self) -> None:
        """nu = 0.499 (near-incompressible) must work."""
        from app import element_stiffness_3d
        Ke = element_stiffness_3d(self.nodes_cube, self.E_standard, nu=0.499)
        self.assertTrue(np.all(np.isfinite(Ke)),
                        "Near-incompressible (nu=0.499) failed")

    def test_degenerate_element_jacobian_zero(self) -> None:
        """Degenerate element (collapsed node) must be handled via detJ regularization."""
        from app import element_stiffness_3d
        # Collapse node 1 into node 0 → Jacobian will be near zero
        nodes_degenerate = self.nodes_cube.copy()
        nodes_degenerate[1] = nodes_degenerate[0]
        Ke = element_stiffness_3d(nodes_degenerate, self.E_standard, self.nu_standard)
        self.assertTrue(np.all(np.isfinite(Ke)),
                        "Degenerate element produced non-finite K (detJ regularization failed)")


class TestHexahedralMesh(unittest.TestCase):
    """Test hexahedral mesh generation."""

    def test_mesh_shape(self) -> None:
        """Mesh should have correct node and element counts."""
        from app import build_hexahedral_mesh
        mesh = build_hexahedral_mesh(nx=5, ny=5, nz=5, lengths=(10.0, 10.0, 10.0))
        # 5×5×5 = 125 nodes
        self.assertEqual(mesh.nodes.shape[0], 125)
        self.assertEqual(mesh.nodes.shape[1], 3)  # 3D coords
        # 4×4×4 = 64 elements
        self.assertEqual(mesh.elements.shape[0], 64)
        self.assertEqual(mesh.elements.shape[1], 8)  # 8 nodes per hex

    def test_mesh_node_bounds(self) -> None:
        """Nodes must be within specified lengths."""
        from app import build_hexahedral_mesh
        mesh = build_hexahedral_mesh(nx=4, ny=3, nz=2, lengths=(10.0, 6.0, 4.0))
        self.assertEqual(mesh.nodes[:, 0].max(), 10.0)
        self.assertEqual(mesh.nodes[:, 1].max(), 6.0)
        self.assertEqual(mesh.nodes[:, 2].max(), 4.0)
        self.assertEqual(mesh.nodes[:, 0].min(), 0.0)
        self.assertEqual(mesh.nodes[:, 1].min(), 0.0)
        self.assertEqual(mesh.nodes[:, 2].min(), 0.0)

    def test_mesh_no_duplicate_nodes(self) -> None:
        """No two nodes should have identical coordinates."""
        from app import build_hexahedral_mesh
        mesh = build_hexahedral_mesh(nx=5, ny=5, nz=5)
        # Round to avoid floating point issues
        rounded = np.round(mesh.nodes, decimals=8)
        unique_count = len(np.unique(rounded, axis=0))
        self.assertEqual(unique_count, mesh.nodes.shape[0],
                         "Duplicate nodes found in mesh")


class TestAdaptiveRefine(unittest.TestCase):
    """Test adaptive mesh refinement (F20 fix)."""

    def setUp(self) -> None:
        from app import build_hexahedral_mesh
        self.mesh = build_hexahedral_mesh(nx=5, ny=5, nz=5)

    def test_refinement_preserves_topology(self) -> None:
        """Refined mesh should have same node count (r-adaptation, not h-refinement)."""
        from app import adaptive_refine_hexahedral_mesh
        indicator = np.random.rand(self.mesh.elements.shape[0])
        refined = adaptive_refine_hexahedral_mesh(self.mesh, indicator, threshold=0.5)
        self.assertEqual(refined.nodes.shape, self.mesh.nodes.shape,
                         "R-adaptation changed node count (should preserve topology)")
        self.assertEqual(refined.elements.shape, self.mesh.elements.shape,
                         "R-adaptation changed element count")

    def test_no_refinement_when_indicator_low(self) -> None:
        """When all indicators are below threshold, mesh should be unchanged."""
        from app import adaptive_refine_hexahedral_mesh
        indicator = np.zeros(self.mesh.elements.shape[0])  # all zero
        refined = adaptive_refine_hexahedral_mesh(self.mesh, indicator, threshold=0.5)
        np.testing.assert_array_equal(refined.nodes, self.mesh.nodes,
                                      "Mesh changed despite no high-error elements")

    def test_nan_indicator_handled(self) -> None:
        """NaN in indicator should not crash (regularized to 0)."""
        from app import adaptive_refine_hexahedral_mesh
        indicator = np.full(self.mesh.elements.shape[0], np.nan)
        indicator[0] = 0.9  # one valid high-error element
        refined = adaptive_refine_hexahedral_mesh(self.mesh, indicator, threshold=0.5)
        self.assertEqual(refined.nodes.shape, self.mesh.nodes.shape,
                         "NaN in indicator caused shape change")

    def test_inf_indicator_handled(self) -> None:
        """Inf in indicator should not crash."""
        from app import adaptive_refine_hexahedral_mesh
        indicator = np.full(self.mesh.elements.shape[0], np.inf)
        refined = adaptive_refine_hexahedral_mesh(self.mesh, indicator, threshold=0.5)
        self.assertEqual(refined.nodes.shape, self.mesh.nodes.shape,
                         "Inf in indicator caused shape change")

    def test_high_error_elements_moved(self) -> None:
        """High-error elements should have their nodes displaced."""
        from app import adaptive_refine_hexahedral_mesh
        indicator = np.zeros(self.mesh.elements.shape[0])
        indicator[:5] = 1.0  # 5 high-error elements
        refined = adaptive_refine_hexahedral_mesh(self.mesh, indicator, threshold=0.5)
        # At least some nodes should have moved
        max_displacement = np.max(np.linalg.norm(refined.nodes - self.mesh.nodes, axis=1))
        self.assertGreater(max_displacement, 0.0,
                           "No nodes moved despite high-error elements")


if __name__ == "__main__":
    unittest.main()
