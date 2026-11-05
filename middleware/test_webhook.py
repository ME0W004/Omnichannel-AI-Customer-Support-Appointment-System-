"""
Mock Webhook Tester for Omnichannel AI Bridge
Run: python test_webhook.py
"""
import sys
import asyncio
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

WEBHOOK_URL = "http://127.0.0.1:8000/webhook/chatwoot"

TEST_CASES = [
    {
        "title": "۱. پیام عادی کاربر (استعلام ساعات کاری)",
        "payload": {
            "event": "message_created",
            "id": 101,
            "content": "سلام، ساعت کاری و روزهای ویزیت کلینیک به چه صورت است؟",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 1, "name": "Ali Rezaei", "type": "contact"},
            "conversation": {"id": 501, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    },
    {
        "title": "۲. درخواست مستقیم اپراتور (کلمه کلیدی فوری)",
        "payload": {
            "event": "message_created",
            "id": 102,
            "content": "لطفاً من رو سریع وصل کن به پشتیبان یا اپراتور انسانی",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 2, "name": "Sara Ahmadi", "type": "contact"},
            "conversation": {"id": 502, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    },
    {
        "title": "۳. شکایت و لحن خشمگین (Sentiment Trigger)",
        "payload": {
            "event": "message_created",
            "id": 103,
            "content": "این چه وضع خدماتیه! دو روزه منتظرم، کلاهبرداریه واقعاً!",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 3, "name": "Mohammad", "type": "contact"},
            "conversation": {"id": 503, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    },
    {
        "title": "۴. بررسی سکوت ربات در مکالمه ارجاع شده (Labeled Conversation)",
        "payload": {
            "event": "message_created",
            "id": 104,
            "content": "الو کسی نیست؟",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 4, "name": "Reza", "type": "contact"},
            "conversation": {"id": 504, "status": "open", "labels": ["human-needed"]},
            "account": {"id": 1}
        }
    },
    {
        "title": "۵. تشخیص نیت نوبت‌دهی (Appointment Intent Routing)",
        "payload": {
            "event": "message_created",
            "id": 105,
            "content": "سلام، من می‌خواستم برای هفته آینده نوبت ویزیت دکتر رزرو کنم.",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 5, "name": "Maryam", "type": "contact"},
            "conversation": {"id": 505, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    }
]

TYPEBOT_WEBHOOK_URL = "http://127.0.0.1:8000/webhook/typebot/appointment"
TYPEBOT_SAMPLE_BOOKING = {
    "conversation_id": None,  # Set to None for pure Google Calendar booking test without Chatwoot mock
    "patient_name": "مریم کریمی",
    "patient_phone": "09123456789",
    "doctor_name": "دکتر متخصص پوست و مو",
    "start_time": "2026-11-10T11:00:00",
    "duration_minutes": 30,
    "notes": "مشاوره اولیه لیزر و ویزیت عمومی"
}


async def run_tests():
    print(f"Testing webhook endpoint at: {WEBHOOK_URL}\n" + "=" * 50)
    async with httpx.AsyncClient() as client:
        for tc in TEST_CASES:
            print(f"\n▶ اجرا: {tc['title']}")
            try:
                res = await client.post(WEBHOOK_URL, json=tc["payload"])
                print(f"  وضعیت پاسخ: {res.status_code} | متن: {res.text}")
            except Exception as e:
                print(f"  خطا در ارسال: {e}")

        print(f"\n▶ اجرا: ۶. تست وبهوک نوبت‌دهی Typebot -> Google Calendar")
        try:
            res = await client.post(TYPEBOT_WEBHOOK_URL, json=TYPEBOT_SAMPLE_BOOKING)
            print(f"  وضعیت پاسخ: {res.status_code} | متن: {res.text}")
        except Exception as e:
            print(f"  خطا در ارسال: {repr(e)}")


if __name__ == "__main__":
    asyncio.run(run_tests())
