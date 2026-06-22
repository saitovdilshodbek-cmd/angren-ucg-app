"""
UCG Platform — Version Management
===================================

Single source of truth for version information.
Endi bitta joyda boshqariladi, hardcoded multiple places emas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


__version__ = "6.0.0"
__author__ = "Saitov Dilshodbek"
__email__ = "saitov@example.com"
__license__ = "Patent Pending — UzPatent DP 2026/00XXX + WIPO PCT/IB2026/00XXXX"
__copyright__ = "© 2026 Saitov Dilshodbek, Tashkent State Technical University"

# Build number: yil+oy+kun formatida
__build_number__ = 20260622


@dataclass(frozen=True)
class VersionInfo:
    """Structured version information."""
    major: int = 6
    minor: int = 0
    patch: int = 0
    prerelease: str = "patent"

    @property
    def full_version(self) -> str:
        """Return full version string: '6.0.0-patent'."""
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        return v

    @property
    def short_version(self) -> str:
        """Return short version: '6.0.0'."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        return self.full_version


# Extension versions (modullar bo'yicha)
VERSION_INFO: Dict[str, str] = {
    "core": __version__,
    "extensions": {
        "patent_v5": "5.0.0",     # F1-F20 (inline in app.py)
        "patent_v6": "6.0.0",     # C1-C16 (in _patent_ext_v6.py)
        "fem": "3.1.0",           # FEM solver
        "pinn": "2.0.0",          # Physics-Informed Neural Network
        "uq": "2.0.0",            # Uncertainty Quantification
        "audit": "1.5.0",         # Audit trail / Merkle chain
    },
    "build": str(__build_number__),
    "python_min": "3.10",
}


# Singleton instance
version_info = VersionInfo()


def get_version_info() -> Dict[str, str]:
    """Return complete version information as a dict."""
    return {
        "version": __version__,
        "build": str(__build_number__),
        "author": __author__,
        "license": __license__,
        "extensions": VERSION_INFO["extensions"],
    }


__all__ = [
    "__version__", "__author__", "__email__", "__license__", "__copyright__",
    "__build_number__", "VersionInfo", "version_info", "VERSION_INFO",
    "get_version_info",
]
