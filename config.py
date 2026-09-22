import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'glowwheels-super-secret-key-2026-carwash')
    
    # Use SQLite locally; supports PostgreSQL (e.g. Supabase, Neon, Render) via DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'glowwheels.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fixed Admin Credentials (per project requirement)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ADMIN_PHONE = os.environ.get('ADMIN_PHONE', '919876543210') # Set your Admin WhatsApp number here

    # Brand Details
    BRAND_NAME = "GlowWheels"
    BRAND_TAGLINE = "Doorstep Mobile Car Wash & Detailing"
    SLOT_START_HOUR = 9   # 9:00 AM
    SLOT_END_HOUR = 18    # 6:00 PM (18:00)

