from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .calendar_store import Appointment
from .memory import Memory


def intent_prompt(message: str, now: datetime, timezone: str) -> str:
    return f"""
You are a Telegram assistant router. Return only valid JSON.
Current datetime: {now.isoformat()}
Timezone: {timezone}

Classify the user message into one action:
- remember: user wants you to remember a stable fact
- add_appointment: user mentions a calendar appointment or event to save
- list_appointments: user asks what is on their calendar
- delete_appointment: user asks to delete an appointment by id
- chat: everything else

JSON schema:
{{
  "action": "remember|add_appointment|list_appointments|delete_appointment|chat",
  "memory": "fact to remember or empty",
  "appointment": {{
    "title": "short title",
    "starts_at": "ISO datetime with timezone",
    "notes": "optional notes"
  }},
  "appointment_id": null
}}

User message:
{message}
""".strip()


def chat_prompt(
    message: str,
    memories: list[Memory],
    appointments: list[Appointment],
    timezone: str,
) -> str:
    memory_text = "\n".join(f"- {item.content}" for item in memories) or "- none"
    appointment_text = (
        "\n".join(f"- #{item.id} {item.starts_at}: {item.title}" for item in appointments)
        or "- none"
    )
    now = datetime.now(ZoneInfo(timezone)).isoformat()
    return f"""
You are a concise personal assistant on Telegram.
Answer naturally and use the stored memory/calendar when relevant.

Current datetime: {now}
Memories:
{memory_text}

Upcoming appointments:
{appointment_text}

User:
{message}
""".strip()


def photo_prompt(
    caption: str,
    memories: list[Memory],
    appointments: list[Appointment],
    timezone: str,
) -> str:
    instruction = caption or "Describe this photo and mention anything useful or notable."
    memory_text = "\n".join(f"- {item.content}" for item in memories) or "- none"
    appointment_text = (
        "\n".join(f"- #{item.id} {item.starts_at}: {item.title}" for item in appointments)
        or "- none"
    )
    now = datetime.now(ZoneInfo(timezone)).isoformat()
    return f"""
You are a concise personal assistant on Telegram.
Answer naturally about the attached photo. Use stored memory/calendar only when relevant.

Current datetime: {now}
Memories:
{memory_text}

Upcoming appointments:
{appointment_text}

User instruction:
{instruction}
""".strip()
