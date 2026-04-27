# run.py
import os
from dotenv import load_dotenv

load_dotenv()

from backend.app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run()