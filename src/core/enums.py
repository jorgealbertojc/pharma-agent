from enum import StrEnum

class Environments(StrEnum):
    DEVELOPMENT: str = "development"
    STAGING: str = "staging"
    PRODUCTION: str = "production"

class LogLevels(StrEnum):
    DEBUG: str = "DEBUG"
    INFO: str = "INFO"
    WARNING: str = "WARNING"
    ERROR: str = "ERROR"
    CRITICAL: str = "CRITICAL"

class IndexMetric(StrEnum):
    COSINE: str = "cosine"
    EUCLIDEAN: str = "euclidean"
    DOTPRODUCT: str = "dotproduct"
