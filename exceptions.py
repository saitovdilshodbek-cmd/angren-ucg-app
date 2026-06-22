"""
UCG Platform — Custom Exception Hierarchy
==========================================

Bu modul barcha UCG platformasi uchun structured exception hierarchy taqdim etadi.
Generic `Exception` ishlatish o'rniga, aniq exception turlari ishlatiladi.

Hierarchy:
    UCGException (base)
    ├── FEMSolverError           — FEM computation errors
    │   ├── FEMMeshError         — Invalid mesh structure
    │   ├── FEMMaterialError     — Invalid material properties
    │   └── FEMConvergenceError  — Solver did not converge
    ├── PatentAnalysisError      — Patent analysis errors
    │   ├── PatentSearchError    — Patent database search errors
    │   └── PatentClaimError     — Claim generation/parsing errors
    ├── ValidationError          — Data validation errors
    ├── ConfigurationError       — Configuration errors
    ├── SecurityError            — Security/crypto errors
    │   ├── KeyManagementError   — RSA key management
    │   └── AuthenticationError  — API authentication
    ├── DatabaseError            — Database operation errors
    └── APIClientError           — External API client errors
        ├── RateLimitError       — Rate limiting (429)
        └── APIConnectionError   — Network/connection errors
"""

from __future__ import annotations


class UCGException(Exception):
    """Base exception for all UCG platform errors."""
    pass


# ── FEM Solver Errors ──────────────────────────────────────────────────
class FEMSolverError(UCGException):
    """Base exception for FEM computation errors."""
    pass


class FEMMeshError(FEMSolverError):
    """Raised when mesh structure is invalid (e.g., negative Jacobian, inverted elements)."""
    pass


class FEMMaterialError(FEMSolverError):
    """Raised when material properties are invalid (e.g., E <= 0, nu not in [0, 0.5])."""
    pass


class FEMConvergenceError(FEMSolverError):
    """Raised when FEM solver fails to converge."""
    pass


# ── Patent Analysis Errors ─────────────────────────────────────────────
class PatentAnalysisError(UCGException):
    """Base exception for patent analysis errors."""
    pass


class PatentSearchError(PatentAnalysisError):
    """Raised when patent database search fails (Google Patents, Espacenet, WIPO)."""
    pass


class PatentClaimError(PatentAnalysisError):
    """Raised when patent claim generation or parsing fails."""
    pass


# ── Validation Errors ──────────────────────────────────────────────────
class ValidationError(UCGException):
    """Raised when input data fails validation."""
    pass


class ConfigurationError(UCGException):
    """Raised when configuration is invalid or missing."""
    pass


# ── Security Errors ────────────────────────────────────────────────────
class SecurityError(UCGException):
    """Base exception for security-related errors."""
    pass


class KeyManagementError(SecurityError):
    """Raised when RSA key management fails (generation, loading, signing)."""
    pass


class AuthenticationError(SecurityError):
    """Raised when API authentication fails (OAuth, API keys)."""
    pass


# ── Database Errors ────────────────────────────────────────────────────
class DatabaseError(UCGException):
    """Raised when database operations fail (SQLite, PostgreSQL, IPFS)."""
    pass


# ── API Client Errors ──────────────────────────────────────────────────
class APIClientError(UCGException):
    """Base exception for external API client errors."""
    pass


class RateLimitError(APIClientError):
    """Raised when API returns 429 (rate limit exceeded)."""
    pass


class APIConnectionError(APIClientError):
    """Raised when network connection to API fails."""
    pass


__all__ = [
    "UCGException",
    "FEMSolverError", "FEMMeshError", "FEMMaterialError", "FEMConvergenceError",
    "PatentAnalysisError", "PatentSearchError", "PatentClaimError",
    "ValidationError", "ConfigurationError",
    "SecurityError", "KeyManagementError", "AuthenticationError",
    "DatabaseError",
    "APIClientError", "RateLimitError", "APIConnectionError",
]
