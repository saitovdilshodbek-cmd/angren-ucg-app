"""
Centralized version management for UCG SCI-Grade Platform.

Bitta joyda boshqariladigan version info — app.py, _patent_ext_v6.py va
boshqa modullar shu yerdan o'qiydi.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class VersionInfo:
    """Semantic version info (PEP 440 compliant)."""
    major: int = 6
    minor: int = 0
    patch: int = 0
    prerelease: str = "patent"

    @property
    def full_version(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        return v

    @property
    def short(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        return self.full_version


# Singleton version instance
version_info = VersionInfo()
__version__ = version_info.full_version
__version_info__ = (version_info.major, version_info.minor, version_info.patch)
__build_number__ = 20260622
__author__ = "Saitov Dilshodbek"
__license__ = "Patent Pending — UzPatent + WIPO PCT"

# Component versions (for granular tracking)
VERSION_INFO: Dict[str, str] = {
    "platform": __version__,
    "core": "6.0.0",
    "fem_solver": "3.1.0",
    "patent_engine": "6.0.0",
    "ai_module": "2.0.0",
    "audit_chain": "1.5.0",
    "extensions": {
        "patent_v5": "5.0.0",
        "patent_v6_critical": "6.0.0",
    },
}


def get_version_info() -> Dict[str, str]:
    """Return full version info as a dict (for logging/UI display)."""
    return {
        "version": __version__,
        "build": str(__build_number__),
        "author": __author__,
        "license": __license__,
        "components": VERSION_INFO,
    }
