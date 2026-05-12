from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import PhotoSize, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .calendar_store import CalendarStore
from .config import load_config
from .llm import LocalLLM
from .memory import MemoryStore
from .prompts import chat_prompt, intent_prompt, photo_prompt


PHOTO_MAX_BYTES = 2_000_000
TELEGRAM_CONNECT_TIMEOUT = 30
TELEGRAM_READ_TIMEOUT = 120


class Agent:
    def __init__(self) -> None:
        self.config = load_config()
        self.llm = LocalLLM(self.config.llm_base_url, self.config.llm_model)
        self.memory = MemoryStore(self.config.database_path)
        self.calendar = CalendarStore(self.config.database_path)
        self.memory.init()
        self.calendar.init()

    def is_allowed(self, update: Update) -> bool:
        if self.config.allowed_telegram_user_id is None:
            return True
        user = update.effective_user
        return bool(user and user.id == self.config.allowed_telegram_user_id)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.is_allowed(update):
            return
        await update.message.reply_text(
            "Ready. I can chat, remember facts, and manage appointments."
        )

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not self.is_allowed(update):
            return
        if update.message is None or not update.message.text:
            return

        message = update.message.text.strip()
        try:
            response = await asyncio.to_thread(self.route_message, message)
        except Exception as error:
            response = f"I hit an error: {error}"
        await update.message.reply_text(response)

    async def handle_photo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not self.is_allowed(update):
            return
        if update.message is None or not update.message.photo:
            return

        photo = self.select_photo(update.message.photo)
        caption = (update.message.caption or "").strip()
        try:
            await update.message.reply_chat_action("typing")
            photo_file = await photo.get_file(
                connect_timeout=TELEGRAM_CONNECT_TIMEOUT,
                read_timeout=TELEGRAM_READ_TIMEOUT,
                pool_timeout=TELEGRAM_CONNECT_TIMEOUT,
            )
            image = bytes(
                await photo_file.download_as_bytearray(
                    connect_timeout=TELEGRAM_CONNECT_TIMEOUT,
                    read_timeout=TELEGRAM_READ_TIMEOUT,
                    pool_timeout=TELEGRAM_CONNECT_TIMEOUT,
                )
            )
        except Exception as error:
            response = f"I timed out while downloading that photo from Telegram: {error}"
            await update.message.reply_text(response)
            return

        try:
            response = await asyncio.to_thread(self.route_photo, caption, image)
        except Exception as error:
            response = f"I downloaded the photo, but hit an error reading it: {error}"
        await update.message.reply_text(response)

    def select_photo(self, photos: tuple[PhotoSize, ...]) -> PhotoSize:
        sized_photos = [photo for photo in photos if photo.file_size is not None]
        small_enough = [
            photo for photo in sized_photos if photo.file_size <= PHOTO_MAX_BYTES
        ]
        candidates = small_enough or sized_photos or list(photos)
        return max(candidates, key=lambda photo: photo.width * photo.height)

    def route_message(self, message: str) -> str:
        now = datetime.now(ZoneInfo(self.config.timezone))
        intent = self.llm.json(intent_prompt(message, now, self.config.timezone))
        action = str(intent.get("action", "chat"))

        if action == "remember":
            memory = str(intent.get("memory", "")).strip() or message
            memory_id = self.memory.add(memory)
            return f"Remembered #{memory_id}: {memory}"

        if action == "add_appointment":
            appointment = intent.get("appointment") or {}
            title = str(appointment.get("title", "")).strip() or message
            starts_at = str(appointment.get("starts_at", "")).strip()
            notes = str(appointment.get("notes", "")).strip()
            if not starts_at:
                return "I could not identify the appointment time."
            appointment_id = self.calendar.add(title, starts_at, notes)
            return f"Added appointment #{appointment_id}: {title} at {starts_at}"

        if action == "list_appointments":
            appointments = self.calendar.upcoming()
            if not appointments:
                return "No upcoming appointments."
            return "\n".join(
                f"#{item.id} {item.starts_at}: {item.title}" for item in appointments
            )

        if action == "delete_appointment":
            appointment_id = intent.get("appointment_id")
            if appointment_id is None:
                return "Tell me the appointment id to delete."
            deleted = self.calendar.delete(int(appointment_id))
            return "Deleted." if deleted else "I could not find that appointment."

        return self.llm.chat(
            chat_prompt(
                message,
                self.memory.recent(),
                self.calendar.upcoming(),
                self.config.timezone,
            )
        )

    def route_photo(self, caption: str, image: bytes) -> str:
        return self.llm.chat_with_image(
            photo_prompt(
                caption,
                self.memory.recent(),
                self.calendar.upcoming(),
                self.config.timezone,
            ),
            image,
            model=self.config.llm_vision_model,
        )


def main() -> None:
    agent = Agent()
    app = Application.builder().token(agent.config.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", agent.start))
    app.add_handler(MessageHandler(filters.PHOTO, agent.handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, agent.handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
