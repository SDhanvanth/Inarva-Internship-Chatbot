"""
Security utilities: JWT, password hashing, encryption, and input sanitization.
"""
import hashlib
import hmac
import html
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64

from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT TOKENS
# =============================================================================

def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> Tuple[str, datetime]:
    """Create a refresh token and return token + expiry."""
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    token = secrets.token_urlsafe(64)
    return token, expire


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# =============================================================================
# ENCRYPTION
# =============================================================================

def get_fernet() -> Fernet:
    """Get Fernet instance for encryption."""
    key = base64.urlsafe_b64encode(settings.ENCRYPTION_KEY[:32].encode().ljust(32, b'\0'))
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a value."""
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a value."""
    f = get_fernet()
    return f.decrypt(encrypted_value.encode()).decode()


# =============================================================================
# INPUT SANITIZATION
# =============================================================================

MAX_INPUT_LENGTH = settings.MAX_INPUT_LENGTH

# Regex patterns for common injections
SQL_INJECTION_PATTERN = re.compile(
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
    re.IGNORECASE
)
SCRIPT_INJECTION_PATTERN = re.compile(
    r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
    re.IGNORECASE | re.DOTALL
)


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    - Removes null bytes
    - Escapes HTML entities
    - Removes control characters (except newlines/tabs)
    - Limits length
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove control characters (except newlines/tabs)
    text = ''.join(c for c in text if c.isprintable() or c in '\n\t\r')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Limit length
    limit = max_length or MAX_INPUT_LENGTH
    return text[:limit]


def sanitize_html(text: str) -> str:
    """Remove all HTML tags from text."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def is_safe_redirect_url(url: str) -> bool:
    """Check if a URL is safe for redirects (no open redirect vulnerability)."""
    if not url:
        return False
    # Only allow relative URLs or same-origin
    return url.startswith('/') and not url.startswith('//')


# =============================================================================
# API REQUEST SIGNING (for MCP)
# =============================================================================

def sign_request(
    endpoint: str,
    method: str,
    body: str,
    timestamp: str
) -> str:
    """Sign an API request for MCP communication."""
    message = f"{method}\n{endpoint}\n{timestamp}\n{body}"
    signature = hmac.new(
        settings.MCP_SIGNING_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(
    endpoint: str,
    method: str,
    body: str,
    timestamp: str,
    signature: str
) -> bool:
    """Verify an API request signature."""
    expected = sign_request(endpoint, method, body, timestamp)
    return hmac.compare_digest(signature, expected)


# =============================================================================
# SECURITY HEADERS
# =============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
