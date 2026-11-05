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
        "title": "1. Standard User Inquiry (Operating Hours & Consultation Info)",
        "payload": {
            "event": "message_created",
            "id": 101,
            "content": "Hello, what are the clinic's operating hours and consultation days?",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 1, "name": "Alexander Wright", "type": "contact"},
            "conversation": {"id": 501, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    },
    {
        "title": "2. Direct Operator Request (Immediate Handoff Keyword)",
        "payload": {
            "event": "message_created",
            "id": 102,
            "content": "Please connect me to a human support agent or operator right away.",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 2, "name": "Emily Watson", "type": "contact"},
            "conversation": {"id": 502, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    },
    {
        "title": "3. Angry Customer Sentiment (Frustration / Dispute Trigger)",
        "payload": {
            "event": "message_created",
            "id": 103,
            "content": "This service is unacceptable! I have been waiting for two days, I want to file a complaint!",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 3, "name": "Michael Brown", "type": "contact"},
            "conversation": {"id": 503, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    },
    {
        "title": "4. Verify Bot Silence on Labeled Conversation (Human-Needed Guard)",
        "payload": {
            "event": "message_created",
            "id": 104,
            "content": "Hello, is anyone there?",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 4, "name": "David Miller", "type": "contact"},
            "conversation": {"id": 504, "status": "open", "labels": ["human-needed"]},
            "account": {"id": 1}
        }
    },
    {
        "title": "5. Appointment Intent Routing (Detects Booking Intent)",
        "payload": {
            "event": "message_created",
            "id": 105,
            "content": "Hi, I would like to schedule an appointment with a specialist for next Tuesday.",
            "message_type": "incoming",
            "private": False,
            "sender": {"id": 5, "name": "Sarah Jenkins", "type": "contact"},
            "conversation": {"id": 505, "status": "open", "labels": []},
            "account": {"id": 1}
        }
    }
]

TYPEBOT_WEBHOOK_URL = "http://127.0.0.1:8000/webhook/typebot/appointment"
TYPEBOT_SAMPLE_BOOKING = {
    "conversation_id": None,  # Set to None for pure Google Calendar booking test without Chatwoot mock
    "patient_name": "Sarah Jenkins",
    "patient_phone": "+1-555-0199",
    "doctor_name": "Dermatology Specialist",
    "start_time": "2026-11-10T11:00:00",
    "duration_minutes": 30,
    "notes": "Initial consultation and skin checkup"
}


async def run_tests():
    print(f"Testing webhook endpoint at: {WEBHOOK_URL}\n" + "=" * 60)
    async with httpx.AsyncClient() as client:
        for tc in TEST_CASES:
            print(f"\n▶ Executing: {tc['title']}")
            try:
                res = await client.post(WEBHOOK_URL, json=tc["payload"])
                print(f"  Response Status: {res.status_code} | Body: {res.text}")
            except Exception as e:
                print(f"  ❌ Error: {e} (Make sure middleware is running at port 8000)")

        print("\n" + "=" * 60)
        print(f"▶ Executing: 6. Automated Calendar Booking via Typebot Webhook")
        try:
            res = await client.post(TYPEBOT_WEBHOOK_URL, json=TYPEBOT_SAMPLE_BOOKING)
            print(f"  Response Status: {res.status_code}")
            print(f"  Booking Result: {res.json()}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("All mock tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())
