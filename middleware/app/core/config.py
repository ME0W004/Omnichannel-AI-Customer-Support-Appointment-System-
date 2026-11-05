from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Omnichannel AI Bridge"
    DEBUG: bool = False
    PORT: int = 8000

    # Chatwoot Configuration
    CHATWOOT_BASE_URL: str = "http://chatwoot-web:3000"
    CHATWOOT_API_ACCESS_TOKEN: str = ""
    CHATWOOT_ACCOUNT_ID: int = 1
    # Bot agent ID or Bot user to ignore loops
    BOT_SENDER_NAME: str = "AI Assistant"

    # Dify Configuration
    DIFY_API_BASE_URL: str = "http://dify-api:5001/v1"
    DIFY_API_KEY: str = ""
    DIFY_TIMEOUT_SECONDS: float = 45.0

    # Google Calendar & Appointments Configuration
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "google-credentials.json"
    CLINIC_TIMEZONE: str = "Asia/Tehran"
    DEFAULT_APPOINTMENT_DURATION_MINUTES: int = 30

    # Typebot Configuration
    TYPEBOT_PUBLIC_URL: str = "https://bot.yourdomain.com/clinic-booking"

    # Appointment Intent Keywords
    APPOINTMENT_KEYWORDS: List[str] = [
        "نوبت",
        "رزرو",
        "وقت ویزیت",
        "گرفتن وقت",
        "تعیین وقت",
        "نوبت دهی",
        "رزرو نوبت",
        "رزرو وقت",
        "وقت دکتر",
        "appointment",
        "booking",
        "book"
    ]

    # Reassurance and appointment links
    APPOINTMENT_REDIRECT_MESSAGE: str = (
        "برای انتخاب پزشک، مشاهده ساعت‌های خالی و ثبت قطعی نوبت در تقویم، "
        "لطفاً روی لینک سامانه نوبت‌دهی کلیک کنید:\n{booking_url}"
    )

    # Zero-Fail Handoff Settings
    HANDOFF_TRIGGER_TOKEN: str = "[TRIGGER_HUMAN_HANDOFF]"
    HANDOFF_KEYWORDS: List[str] = [
        "پشتیبان",
        "اپراتور",
        "وصل کن به انسان",
        "انسان",
        "کارشناس",
        "شکایت",
        "اورژانس",
        "دکتر متخصص",
        "دعوا",
        "کلاهبرداری",
        "human",
        "agent",
        "operator",
        "support",
        "complaint",
        "emergency"
    ]

    HANDOFF_LABEL: str = "human-needed"
    HANDOFF_ASSIGNED_TEAM_ID: int = 0  # 0 means unassigned or default team

    # Reassurance message to user in Persian
    HANDOFF_USER_MESSAGE: str = (
        "پیام شما به تیم کارشناسان و پشتیبانی منتقل شد. همکاران ما به زودی گفتگو را ادامه خواهند داد. سپاس از شکیبایی شما."
    )

    # Fallback message if AI fails
    FALLBACK_ERROR_MESSAGE: str = (
        "متأسفانه در پردازش هوشمند اختلالی پیش آمد. مکالمه فوراً به اپراتور انسانی ارجاع داده شد."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
