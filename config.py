from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{INSTANCE_DIR / 'normalized_sales.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Source dump containing the universal relation `sales`
    SOURCE_DB_PATH = Path(os.getenv("SOURCE_DB_PATH", str(BASE_DIR / "sales_dump.db")))
    SOURCE_TABLE_NAME = os.getenv("SOURCE_TABLE_NAME", "sales")
