from pydantic_settings import BaseSettings
from typing import List, Literal
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment-based security"""
    
    # Environment (CRITICAL for security)
    APP_ENV: Literal["local", "staging", "production"] = "local"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = ""
    
    # Security
    SECRET_KEY: str  # JWT secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Development bypass (DANGEROUS - production override below)
    DEV_BYPASS_AUTH: bool = False
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"
    
    # Application
    APP_NAME: str = "CyberCafe POS Pro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # M-Pesa Daraja
    MPESA_CONSUMER_KEY: str = ""
    MPESA_CONSUMER_SECRET: str = ""
    MPESA_SHORTCODE: str = ""
    MPESA_PASSKEY: str = ""
    MPESA_ENVIRONMENT: str = "sandbox"  # sandbox or production
    MPESA_CALLBACK_URL: str = ""  # Public URL for callbacks
    MPESA_ALLOWED_IPS: str = ""  # Comma-separated Safaricom IPs for callback validation
    
    # File Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_TYPES: str = "application/pdf,image/jpeg,image/png,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    # Health Check
    HEALTH_CHECK_TOKEN: str = ""
    
    @validator("APP_ENV")
    def validate_app_env(cls, v):
        """Validate APP_ENV"""
        allowed = ["local", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v
    
    @validator("DEV_BYPASS_AUTH")
    def validate_dev_bypass(cls, v, values):
        """CRITICAL: Force DEV_BYPASS_AUTH=False in staging/production"""
        app_env = values.get("APP_ENV", "local")
        
        if app_env in ["staging", "production"]:
            if v is True:
                raise ValueError(
                    f"SECURITY VIOLATION: DEV_BYPASS_AUTH cannot be True in {app_env} environment. "
                    "This is a hard override for security."
                )
            return False  # Force False
        
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """Validate SECRET_KEY strength"""
        app_env = values.get("APP_ENV", "local")
        
        if not v:
            raise ValueError("SECRET_KEY is required")
        
        # In production/staging, enforce strong secret
        if app_env in ["staging", "production"]:
            if len(v) < 32:
                raise ValueError(
                    f"SECRET_KEY must be at least 32 characters in {app_env} environment. "
                    f"Current length: {len(v)}"
                )
            
            # Check if it's a weak/default secret
            weak_secrets = ["secret", "password", "changeme", "default", "test"]
            if v.lower() in weak_secrets:
                raise ValueError(
                    f"SECRET_KEY appears to be a weak/default value in {app_env} environment"
                )
        
        return v
    
    @validator("CORS_ORIGINS")
    def validate_cors(cls, v, values):
        """Validate CORS configuration"""
        app_env = values.get("APP_ENV", "local")
        
        # In production, warn about wildcard CORS
        if app_env == "production" and v == "*":
            print(
                "WARNING: CORS_ORIGINS is set to '*' in production. "
                "Consider restricting to specific origins for security."
            )
        
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def get_mpesa_allowed_ips(self) -> List[str]:
        """Get M-Pesa allowed IPs as list"""
        if not self.MPESA_ALLOWED_IPS:
            return []
        return [ip.strip() for ip in self.MPESA_ALLOWED_IPS.split(",")]
    
    def get_allowed_upload_types(self) -> List[str]:
        """Get allowed upload MIME types as list"""
        return [mime.strip() for mime in self.ALLOWED_UPLOAD_TYPES.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


def validate_production_config(settings: Settings):
    """
    Perform additional production safety checks
    Called at application startup
    """
    errors = []
    warnings = []
    
    # Check 1: DEV_BYPASS_AUTH must be False in production/staging
    if settings.APP_ENV in ["staging", "production"] and settings.DEV_BYPASS_AUTH:
        errors.append(
            f"CRITICAL: DEV_BYPASS_AUTH is True in {settings.APP_ENV} environment. "
            "Application startup blocked for security."
        )
    
    # Check 2: SECRET_KEY must be strong
    if len(settings.SECRET_KEY) < 32:
        if settings.APP_ENV in ["staging", "production"]:
            errors.append(
                f"CRITICAL: SECRET_KEY is too weak ({len(settings.SECRET_KEY)} chars). "
                "Minimum 32 characters required in {settings.APP_ENV}."
            )
        else:
            warnings.append(
                f"WARNING: SECRET_KEY is weak ({len(settings.SECRET_KEY)} chars). "
                "Consider using at least 32 characters."
            )
    
    # Check 3: Database URL must be set
    if not settings.DATABASE_URL:
        errors.append("CRITICAL: DATABASE_URL is not set")
    
    # Check 4: In production, HTTPS should be used
    if settings.APP_ENV == "production":
        if settings.MPESA_CALLBACK_URL and not settings.MPESA_CALLBACK_URL.startswith("https://"):
            warnings.append(
                "WARNING: MPESA_CALLBACK_URL should use HTTPS in production"
            )
    
    # Check 5: M-Pesa IP allowlist in production
    if settings.APP_ENV in ["staging", "production"] and not settings.MPESA_ALLOWED_IPS:
        warnings.append(
            "WARNING: MPESA_ALLOWED_IPS is empty. "
            "M-Pesa callbacks will not be IP-restricted. "
            "Add Safaricom IPs for better security."
        )
    
    # Print warnings
    if warnings:
        print("\nConfiguration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # If any critical errors, raise exception
    if errors:
        error_msg = "\n".join(f"  - {err}" for err in errors)
        raise RuntimeError(
            f"\nProduction configuration validation failed:\n{error_msg}\n\n"
            "Fix these issues before starting the application."
        )
    
    print(f"Configuration validated for {settings.APP_ENV} environment")


settings = Settings()

