"""
Custom exception hierarchy for UCG SCI-Grade Platform.

Har bir exception aniq kategoriya uchun — bu exception handling ni aniq va
debuggable qiladi. Generic `Exception` ishlatish o'rniga, aniq exception
type larni catch qilish mumkin.

Hierarchy:
    UCGException (base)
    ├── FEMSolverError
    │   ├── FEMMeshError
    │   └── FEMConvergenceError
    ├── PatentAnalysisError
    │   ├── PatentSearchError
    │   └── PatentClaimError
    ├── ValidationError
    ├── ConfigurationError
    ├── SecurityError
    │   ├── KeyManagementError
    │   └── AuthenticationError
    ├── DataError
    │   ├── DatasetError
    │   └── ModelError
    └── APIError
        ├── GooglePatentsAPIError
        ├── EspacenetAPIError
        └── CrossrefAPIError
"""

from __future__ import annotations
from typing import Optional


class UCGException(Exception):
    """Base exception for all UCG platform errors."""

    def __init__(self, message: str, *, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message} (detail: {self.detail})"
        return self.message


# ── FEM Solver errors ──────────────────────────────────────────────────────
class FEMSolverError(UCGException):
    """FEM computation error (generic)."""
    pass


class FEMMeshError(FEMSolverError):
    """Invalid mesh structure (degenerate elements, negative Jacobian, etc.)."""
    pass


class FEMMaterialError(FEMSolverError):
    """Invalid material properties (E ≤ 0, nu out of [-1, 0.5], etc.)."""
    pass


class FEMConvergenceError(FEMSolverError):
    """FEM solver failed to converge."""
    pass


# ── Patent analysis errors ─────────────────────────────────────────────────
class PatentAnalysisError(UCGException):
    """Patent analysis error (generic)."""
    pass


class PatentSearchError(PatentAnalysisError):
    """Patent database search error (Google Patents, Espacenet, WIPO, Crossref)."""
    pass


class PatentClaimError(PatentAnalysisError):
    """Patent claim generation/parsing error."""
    pass


# ── Validation errors ──────────────────────────────────────────────────────
class ValidationError(UCGException):
    """Data validation error (invalid input, out-of-range values, etc.)."""
    pass


class ConfigurationError(UCGException):
    """Configuration error (missing env vars, invalid config, etc.)."""
    pass


# ── Security errors ────────────────────────────────────────────────────────
class SecurityError(UCGException):
    """Security-related error (cryptography, signing, etc.)."""
    pass


class KeyManagementError(SecurityError):
    """RSA/PQC key management error (key generation, loading, signing)."""
    pass


class AuthenticationError(SecurityError):
    """Authentication error (API keys, OAuth tokens, etc.)."""
    pass


# ── Data errors ────────────────────────────────────────────────────────────
class DataError(UCGException):
    """Data-related error (database, file I/O, etc.)."""
    pass


class DatasetError(DataError):
    """Dataset error (missing data, corrupt data, etc.)."""
    pass


class ModelError(DataError):
    """Model error (serialization, loading, inference)."""
    pass


# ── API errors ─────────────────────────────────────────────────────────────
class APIError(UCGException):
    """External API error (HTTP, network, rate limit)."""

    def __init__(self, message: str, *, status_code: Optional[int] = None,
                 endpoint: Optional[str] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"HTTP {self.status_code}")
        if self.endpoint:
            parts.append(f"endpoint={self.endpoint}")
        return " | ".join(parts)


class GooglePatentsAPIError(APIError):
    """Google Patents API error."""
    pass


class EspacenetAPIError(APIError):
    """Espacenet OPS API error."""
    pass


class WIPOAPIError(APIError):
    """WIPO Patentscope API error."""
    pass


class CrossrefAPIError(APIError):
    """Crossref API error."""
    pass


class DataCiteAPIError(APIError):
    """DataCite REST API error."""
    pass
