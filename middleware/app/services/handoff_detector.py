import re
from typing import Optional, Tuple
from app.core.config import settings


class HandoffDetector:
    def __init__(self):
        # 1. Critical Handoff pattern (emergency, anger, human request)
        self.handoff_keywords = [
            k.strip().lower() for k in settings.HANDOFF_KEYWORDS if k.strip()
        ]
        handoff_pattern_str = r"(" + "|".join(re.escape(k) for k in self.handoff_keywords) + r")"
        self.handoff_regex = re.compile(handoff_pattern_str, re.IGNORECASE | re.UNICODE)

        # 2. Appointment Booking pattern
        self.appointment_keywords = [
            k.strip().lower() for k in settings.APPOINTMENT_KEYWORDS if k.strip()
        ]
        apt_pattern_str = r"(" + "|".join(re.escape(k) for k in self.appointment_keywords) + r")"
        self.appointment_regex = re.compile(apt_pattern_str, re.IGNORECASE | re.UNICODE)

    def check_direct_keyword(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Quick synchronous check if user explicitly requested an operator
        or used an emergency/anger trigger word.
        """
        if not text:
            return False, None

        cleaned_text = text.strip().lower()
        match = self.handoff_regex.search(cleaned_text)
        if match:
            found_word = match.group(1)
            return True, f"Critical keyword detected: '{found_word}'"

        return False, None

    def check_appointment_intent(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Detects if user is asking to book an appointment or visit a specialist.
        """
        if not text:
            return False, None

        cleaned_text = text.strip().lower()
        match = self.appointment_regex.search(cleaned_text)
        if match:
            found_word = match.group(1)
            return True, f"Appointment intent detected: '{found_word}'"

        return False, None


handoff_detector = HandoffDetector()
