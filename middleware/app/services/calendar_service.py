import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Google API Client imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    logger.warning("Google API client libraries not installed or failed to import.")


class GoogleCalendarService:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self):
        self.calendar_id = settings.GOOGLE_CALENDAR_ID
        self.timezone = settings.CLINIC_TIMEZONE
        self.credentials_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service

        if not GOOGLE_LIBS_AVAILABLE:
            logger.error("google-api-python-client is required for Google Calendar integration.")
            return None

        if not os.path.exists(self.credentials_path):
            logger.warning(
                "Google Service Account file '%s' not found. Calendar operations will run in simulated mode.",
                self.credentials_path,
            )
            return None

        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=self.SCOPES
            )
            self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            logger.info("Successfully authenticated with Google Calendar API.")
            return self._service
        except Exception as e:
            logger.exception("Failed to initialize Google Calendar client: %s", e)
            return None

    def create_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        start_time_iso: str,
        duration_minutes: Optional[int] = None,
        doctor_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates an appointment event in Google Calendar.
        If credentials are not yet mounted on the server, returns a simulated success response for staging.
        """
        service = self._get_service()
        duration = duration_minutes or settings.DEFAULT_APPOINTMENT_DURATION_MINUTES

        # Parse start and calculate end time
        try:
            start_dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
            end_dt = start_dt + timedelta(minutes=duration)
            end_time_iso = end_dt.isoformat()
        except Exception:
            start_dt = datetime.now()
            end_dt = start_dt + timedelta(minutes=duration)
            start_time_iso = start_dt.isoformat()
            end_time_iso = end_dt.isoformat()

        doc = doctor_name or "پزشک معالج / متخصص"
        summary = f"نوبت ویزیت: {patient_name} - {doc}"
        description = (
            f"سامانه نوبت‌دهی خودکار کلینیک\n"
            f"نام بیمار: {patient_name}\n"
            f"شماره تماس: {patient_phone}\n"
            f"پزشک: {doc}\n"
            f"توضیحات/علائم اولیه: {notes or 'ثبت شده از طریق چت‌بات هوشمند'}"
        )

        event_body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time_iso,
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": end_time_iso,
                "timeZone": self.timezone,
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "popup", "minutes": 24 * 60},
                ],
            },
        }

        if service is None:
            logger.info(
                "[SIMULATION] Google Calendar appointment booked for %s at %s (%s)",
                patient_name,
                start_time_iso,
                summary,
            )
            return {
                "success": True,
                "mode": "simulation",
                "event_id": f"sim_{int(datetime.now().timestamp())}",
                "html_link": "https://calendar.google.com",
                "start_time": start_time_iso,
                "end_time": end_time_iso,
                "summary": summary,
            }

        try:
            created_event = (
                service.events()
                .insert(calendarId=self.calendar_id, body=event_body)
                .execute()
            )
            logger.info("Created Google Calendar event ID: %s", created_event.get("id"))
            return {
                "success": True,
                "mode": "live",
                "event_id": created_event.get("id"),
                "html_link": created_event.get("htmlLink"),
                "start_time": start_time_iso,
                "end_time": end_time_iso,
                "summary": summary,
            }
        except Exception as e:
            logger.exception("Error creating event in Google Calendar: %s", e)
            return {
                "success": False,
                "error": str(e),
                "summary": summary,
            }

    def get_busy_intervals(self, time_min_iso: str, time_max_iso: str) -> List[Dict[str, str]]:
        """Queries Google Calendar FreeBusy API to find occupied slots."""
        service = self._get_service()
        if not service:
            return []

        body = {
            "timeMin": time_min_iso,
            "timeMax": time_max_iso,
            "timeZone": self.timezone,
            "items": [{"id": self.calendar_id}],
        }

        try:
            freebusy_result = service.freebusy().query(body=body).execute()
            calendars = freebusy_result.get("calendars", {})
            return calendars.get(self.calendar_id, {}).get("busy", [])
        except Exception as e:
            logger.exception("Error checking busy slots in Google Calendar: %s", e)
            return []


calendar_service = GoogleCalendarService()
