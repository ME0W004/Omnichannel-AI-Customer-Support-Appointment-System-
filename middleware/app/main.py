import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, status, Query
from app.core.config import settings
from app.schemas.chatwoot import ChatwootWebhookPayload
from app.services.chatwoot_client import chatwoot_client
from app.services.dify_client import dify_client
from app.services.handoff_detector import handoff_detector
from app.services.calendar_service import calendar_service

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("middleware")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)


class TypebotBookingPayload(BaseModel):
    conversation_id: Optional[int] = None
    patient_name: str
    patient_phone: str
    start_time: str
    duration_minutes: Optional[int] = 30
    doctor_name: Optional[str] = None
    notes: Optional[str] = None


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "chatwoot_configured": bool(settings.CHATWOOT_API_ACCESS_TOKEN),
        "dify_configured": bool(settings.DIFY_API_KEY),
        "google_calendar_configured": bool(settings.GOOGLE_CALENDAR_ID),
    }


@app.post("/webhook/typebot/appointment", status_code=status.HTTP_200_OK)
async def typebot_appointment_webhook(payload: TypebotBookingPayload):
    """
    Called by Typebot after patient selects time slot and completes intake form.
    Inserts event into Google Calendar and updates Chatwoot conversation.
    """
    logger.info("Received appointment booking from Typebot for: %s", payload.patient_name)

    # 1. Book in Google Calendar
    result = calendar_service.create_appointment(
        patient_name=payload.patient_name,
        patient_phone=payload.patient_phone,
        start_time_iso=payload.start_time,
        duration_minutes=payload.duration_minutes,
        doctor_name=payload.doctor_name,
        notes=payload.notes,
    )

    # 2. If conversation_id is provided, notify Chatwoot and update status
    if payload.conversation_id:
        conv_id = payload.conversation_id
        if result.get("success"):
            # Success confirmation message
            conf_msg = (
                f"✅ Your appointment has been successfully scheduled and booked on the calendar.\n"
                f"👤 Patient: {payload.patient_name}\n"
                f"🩺 Specialist: {payload.doctor_name or 'Clinic Specialist'}\n"
                f"📅 Date & Time: {payload.start_time}\n"
                f"Confirmation Code: {result.get('event_id')}"
            )
            await chatwoot_client.send_message(conv_id, conf_msg, message_type="outgoing")
            await chatwoot_client.add_labels(conv_id, ["appointment-booked"])

            # Staff private note
            staff_note = (
                f"📌 [New Google Calendar Appointment Booked]\n"
                f"Patient: {payload.patient_name} ({payload.patient_phone})\n"
                f"Doctor / Specialist: {payload.doctor_name}\n"
                f"Calendar Event Link: {result.get('html_link')}"
            )
            await chatwoot_client.send_message(conv_id, staff_note, message_type="outgoing", private=True)
        else:
            err_msg = (
                "An error occurred while scheduling your calendar appointment. "
                "Your inquiry has been transferred to our front desk reception."
            )
            await chatwoot_client.trigger_human_handoff(
                conv_id,
                reason=f"Calendar booking error: {result.get('error')}",
                user_notice=err_msg,
            )

    return result


async def process_chatwoot_event(payload: ChatwootWebhookPayload):
    """
    Background worker that handles Chatwoot events asynchronously,
    preventing webhook timeouts.
    """
    event = payload.event
    if event != "message_created":
        logger.debug("Skipping unhandled event: %s", event)
        return

    # 1. Ignore outgoing messages and internal staff notes
    if payload.message_type != "incoming":
        logger.debug("Skipping non-incoming message (%s)", payload.message_type)
        return

    if payload.private:
        logger.debug("Skipping private note")
        return

    conversation = payload.conversation
    if not conversation:
        logger.warning("Payload missing conversation object")
        return

    conversation_id = conversation.id
    user_message = (payload.content or "").strip()

    if not user_message:
        logger.debug("Empty message content received. Ignoring.")
        return

    # 2. Check if conversation is already handed over to a human
    current_labels = conversation.labels or []
    if settings.HANDOFF_LABEL in current_labels:
        logger.info(
            "Conversation %s is already marked with '%s'. Bot will remain silent.",
            conversation_id,
            settings.HANDOFF_LABEL,
        )
        return

    # 3. Check for immediate handoff keywords (Rule-based Fast Filter)
    is_direct_handoff, handoff_reason = handoff_detector.check_direct_keyword(user_message)
    if is_direct_handoff:
        await chatwoot_client.trigger_human_handoff(
            conversation_id=conversation_id,
            reason=f"Direct customer request: {handoff_reason}",
        )
        return

    # 4. Check for Appointment Booking Intent
    is_appointment, apt_reason = handoff_detector.check_appointment_intent(user_message)
    if is_appointment:
        logger.info("Appointment intent detected for conv %s: %s", conversation_id, apt_reason)
        # Generate personalized booking link with conversation ID
        booking_url = f"{settings.TYPEBOT_PUBLIC_URL}?cid={conversation_id}"
        reply_text = settings.APPOINTMENT_REDIRECT_MESSAGE.format(booking_url=booking_url)

        await chatwoot_client.send_message(conversation_id, reply_text, message_type="outgoing")
        await chatwoot_client.add_labels(conversation_id, ["appointment-pending"])
        return

    # 5. Route to Dify AI Brain (RAG + Agent)
    user_identifier = (
        f"contact_{payload.sender.id}" if payload.sender and payload.sender.id else f"conv_{conversation_id}"
    )

    ai_answer, _, handoff_triggered = await dify_client.chat_message(
        query=user_message,
        user_id=user_identifier,
        conversation_id=str(conversation_id),
    )

    # 6. Handle Dify Response
    if handoff_triggered:
        await chatwoot_client.trigger_human_handoff(
            conversation_id=conversation_id,
            reason="Knowledge base mismatch (RAG Fallback) or negative sentiment detected",
        )
        return

    if ai_answer:
        # Deliver verified AI answer to user
        await chatwoot_client.send_message(
            conversation_id=conversation_id,
            content=ai_answer,
            message_type="outgoing",
            private=False,
        )
    else:
        # Fail-safe: If answer is empty or unexpected failure, handoff immediately
        await chatwoot_client.trigger_human_handoff(
            conversation_id=conversation_id,
            reason="No valid response received from AI engine (Fail-Safe to Human)",
            user_notice=settings.FALLBACK_ERROR_MESSAGE,
        )


@app.post("/webhook/chatwoot", status_code=status.HTTP_200_OK)
async def chatwoot_webhook(
    payload: ChatwootWebhookPayload, background_tasks: BackgroundTasks
):
    """
    Accepts Chatwoot webhooks immediately (200 OK) and processes the payload
    in background tasks to prevent HTTP connection drops.
    """
    background_tasks.add_task(process_chatwoot_event, payload)
    return {"status": "queued"}
