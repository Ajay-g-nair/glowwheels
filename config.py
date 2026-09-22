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
    
    if not database_url:
        bundled_db = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'glowwheels.db')
        # In Vercel or AWS Lambda environments, root filesystem is read-only; use writable /tmp/
        if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or (os.name != 'nt' and os.path.exists('/tmp')):
            tmp_db = '/tmp/glowwheels.db'

            # If tmp_db does not exist, is empty, or is not writable, copy cleanly from bundled_db
            should_copy = False
            if not os.path.exists(tmp_db) or os.path.getsize(tmp_db) == 0:
                should_copy = True
            elif not os.access(tmp_db, os.W_OK):
                try:
                    os.chmod(tmp_db, 0o666)
                except Exception:
                    pass
                if not os.access(tmp_db, os.W_OK):
                    try:
                        os.remove(tmp_db)
                        should_copy = True
                    except Exception:
                        pass

            if should_copy and os.path.exists(bundled_db):
                import shutil
                try:
                    shutil.copyfile(bundled_db, tmp_db)
                except Exception:
                    pass

            # Explicitly grant read/write permissions (mode 0666) to the db and any SQLite journal/wal files
            for ext in ['', '-journal', '-wal', '-shm']:
                target = f"{tmp_db}{ext}"
                if os.path.exists(target):
                    try:
                        os.chmod(target, 0o666)
                    except Exception:
                        pass
            sqlite_path = tmp_db
        else:
            sqlite_path = bundled_db
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"
    else:
        SQLALCHEMY_DATABASE_URI = database_url

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

