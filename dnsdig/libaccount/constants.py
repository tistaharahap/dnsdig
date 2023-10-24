from enum import Enum


class TokenTypes(str, Enum):
    M2M = "m2m"
    M2MRefreshToken = "m2m_refresh_token"


class TokenLifetimes(int, Enum):
    M2M = 60 * 60 * 24
    M2MRefreshToken = 60 * 60 * 24 * 30
