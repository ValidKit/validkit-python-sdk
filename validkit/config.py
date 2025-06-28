"""Configuration for ValidKit SDK"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ValidKitConfig:
    """Configuration for ValidKit client"""
    
    api_key: str
    base_url: str = "https://api.validkit.com"
    api_version: str = "v1"
    timeout: int = 30  # seconds
    max_retries: int = 3
    max_connections: int = 100
    max_keepalive_connections: int = 20
    rate_limit: Optional[int] = None  # requests per minute
    
    # Agent-specific settings
    user_agent: str = "ValidKit-Python/1.0.0"
    enable_compression: bool = True
    compact_format: bool = True  # Use token-efficient format by default
    
    # Batch settings
    default_chunk_size: int = 1000
    max_batch_size: int = 10000
    
    # Webhook settings
    webhook_timeout: int = 300  # 5 minutes for large batches
    
    # Headers
    extra_headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("API key is required")
        
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        
        if self.rate_limit is not None and self.rate_limit <= 0:
            raise ValueError("Rate limit must be positive")
    
    @property
    def api_url(self) -> str:
        """Get full API URL"""
        return f"{self.base_url.rstrip('/')}/api/{self.api_version}"
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get default headers"""
        headers = {
            "User-Agent": self.user_agent,
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.enable_compression:
            headers["Accept-Encoding"] = "gzip, deflate"
        
        headers.update(self.extra_headers)
        return headers