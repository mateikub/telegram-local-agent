# Telegram Local Agent

Small Telegram assistant that uses a local OpenAI-compatible LLM endpoint and stores memory plus calendar appointments in SQLite.

## Setup

1. Create a Telegram bot with `@BotFather` and copy the token.
2. Start LM Studio or another OpenAI-compatible local server at `http://127.0.0.1:1234`.
3. Install dependencies:

```bash
cd /Users/matuk/PyCharmMiscProject/telegram_local_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

4. Configure environment:

```bash
cp .env.example .env
```

Edit `.env` and set `TELEGRAM_BOT_TOKEN`.

Optional but recommended: set `ALLOWED_TELEGRAM_USER_ID` to your Telegram numeric user id so only you can use the bot.

To answer photo messages, use a local model that supports vision. Set `LLM_VISION_MODEL` if it is different from `LLM_MODEL`.

## Run

```bash
./run_agent.sh
```

Windows PowerShell:

```powershell
.\run_agent.ps1
```

## What It Can Do

- Chat through Telegram using your local LLM.
- Answer questions about photos sent through Telegram, when your local model supports images.
- Remember facts you explicitly tell it.
- Add appointments from natural language.
- List upcoming appointments.
- Delete appointments by id.

Example messages:

```text
remember that my dentist is Dr. Popescu
tomorrow at 10 dentist appointment
what do I have today?
delete appointment 3
what do you remember about my dentist?
```

Data is stored locally in `data/agent.sqlite3`.
