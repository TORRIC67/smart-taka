"""All settings come from the .env file (or real environment variables)."""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./smarttaka.db"
    SECRET_KEY: str  # required: the app will not start without it
    ACCESS_TOKEN_MINUTES: int = 60 * 8
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]  # your React dev server
    APP_URL: str = "http://localhost:5173"  # link customers get in the billing SMS

    # ---- payments ----
    PAYMENT_PROVIDER: str = "harakapay"  # "harakapay" (real) or "mock" (fake, development only)
    HARAKAPAY_API_KEY: str = ""
    HARAKAPAY_BASE_URL: str = "https://harakapay.net"
    HARAKAPAY_WEBHOOK_TOKEN: str = ""
    HARAKAPAY_WEBHOOK_URL: str = ""
    MONTHLY_FEE_TZS: int = 200  # testing value - set the real fee in .env

    # ---- SMS (Briq) ----
    SMS_PROVIDER: str = "briq"  # "briq", "meseji" (real) or "mock" (prints the SMS in the server console)
    BRIQ_API_KEY: str = ""
    BRIQ_BASE_URL: str = "https://karibu.briq.tz"
    BRIQ_SENDER_ID: str = "BRIQ"  # use your approved sender ID
    MESEJI_API_KEY: str = ""
    MESEJI_BASE_URL: str = "https://meseji.co.tz/api/v1"
    MESEJI_SENDER_ID: str = "MESEJI"  # "MESEJI" is the default sender available to everyone; use your own once approved

    # ---- IoT bin sensors ----
    SENSOR_API_KEY: str = ""  # sensors send this in the X-Sensor-Key header. Empty = sensors are refused.
    BIN_FULL_THRESHOLD: int = 80  # % fill level at which a bin counts as "full"

    # ---- route optimization ----
    DEPOT_LATITUDE: float = -6.838848  # where trucks start and end the day - SET YOUR REAL DEPOT
    DEPOT_LONGITUDE: float = 39.271071
    FUEL_PRICE_TZS_PER_LITER: int = 3000  # PLACEHOLDER - set today's real pump price
    TRIP_FIXED_COST_TZS: int = 0          # optional extra cost per trip (driver allowance, etc.)
    STOP_SERVICE_MINUTES: int = 3         # time spent at each stop (placeholder)
    ROAD_FACTOR: float = 1.3              # estimate: road distance = straight line x this
    AVG_SPEED_KMH: float = 25.0           # estimate only: average city speed


settings = Settings()
