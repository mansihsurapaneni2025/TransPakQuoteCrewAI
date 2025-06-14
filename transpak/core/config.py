"""
Configuration management for TransPak AI Quoter
"""

import os
from typing import Dict, Any


class Config:
    """Base configuration class"""
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
    }
    
    # Security
    SECRET_KEY = os.environ.get("SESSION_SECRET")
    
    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o"
    
    # Redis Cache
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    
    # Logging
    LOG_LEVEL = "DEBUG"
    
    # Pricing Configuration
    PRICING_CONFIG = {
        "base_rate_per_lb": 1.50,
        "fuel_surcharge_rate": 0.18,
        "insurance_base_rate": 0.015,
        "labor_rate_per_hour": 45,
        "fragility_multipliers": {
            "Standard": 1.0,
            "Fragile": 1.3,
            "High Value": 1.5,
            "Extremely Fragile": 1.8
        }
    }
    
    # MCP Connector Configuration
    MCP_CONFIG = {
        "enabled_carriers": ["FedEx", "UPS", "DHL", "USPS"],
        "timeout": 30,
        "retry_attempts": 3
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}