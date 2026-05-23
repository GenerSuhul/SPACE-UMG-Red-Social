# run.py
import os
from dotenv import load_dotenv

load_dotenv()

from backend.app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 5000))
    debug = os.getenv("BACKEND_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)