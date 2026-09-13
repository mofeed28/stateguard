"""StateGuard backend package."""
from pathlib import Path
from dotenv import load_dotenv

# Explicit process settings take precedence; never expose dotenv through the UI.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
