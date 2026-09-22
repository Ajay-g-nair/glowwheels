import sys
import os

# Add root directory to sys.path so imports work properly in serverless environments
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

# Vercel requires the WSGI app instance to be named `app`

