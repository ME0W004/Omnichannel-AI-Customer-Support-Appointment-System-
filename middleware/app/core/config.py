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
    # Bot agent name or sender to ignore echo loops
    BOT_SENDER_NAME: str = "AI Assistant"

    # Dify Configuration
    DIFY_API_BASE_URL: str = "http://dify-api:5001/v1"
    DIFY_API_KEY: str = ""
    DIFY_TIMEOUT_SECONDS: float = 45.0

    # Google Calendar & Appointments Configuration
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "google-credentials.json"
    CLINIC_TIMEZONE: str = "UTC"
    DEFAULT_APPOINTMENT_DURATION_MINUTES: int = 30

    # Typebot Configuration
    TYPEBOT_PUBLIC_URL: str = "https://bot.yourdomain.com/clinic-booking"

    # Appointment Intent Keywords
    APPOINTMENT_KEYWORDS: List[str] = [
        "appointment",
        "booking",
        "book",
        "schedule",
        "reserve",
        "reservation",
        "consultation",
        "doctor",
        "visit",
        "slot",
    ]

    # Reassurance and appointment links
    APPOINTMENT_REDIRECT_MESSAGE: str = (
        "To select your specialist, view available time slots, and confirm your booking on our calendar, "
        "please click our scheduling portal:\n{booking_url}"
    )

    # Zero-Fail Handoff Settings
    HANDOFF_TRIGGER_TOKEN: str = "[TRIGGER_HUMAN_HANDOFF]"
    HANDOFF_KEYWORDS: List[str] = [
        "human",
        "agent",
        "operator",
        "support",
        "representative",
        "person",
        "real person",
        "talk to human",
        "complaint",
        "emergency",
        "urgent",
        "manager",
        "supervisor",
        "helpdesk",
        "fraud",
        "dispute",
    ]

    HANDOFF_LABEL: str = "human-needed"
    HANDOFF_ASSIGNED_TEAM_ID: int = 0  # 0 means unassigned or default team

    # Reassurance message to user in English
    HANDOFF_USER_MESSAGE: str = (
        "Your conversation has been transferred to our live support team. "
        "A representative will join shortly. Thank you for your patience."
    )

    # Fallback message if AI fails
    FALLBACK_ERROR_MESSAGE: str = (
        "We encountered a temporary issue processing your request with our automated assistant. "
        "You have been immediately transferred to a human representative."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
