# Namoz Time & Islamic Assistant Bot

Production-ready Telegram bot for prayer times, reminders, qibla, Hijri date, duas, tasbeh, and multilingual UX (UZ/RU/EN).

## Local Run (Development)
1. Create a virtualenv and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create `.env` based on `.env.example`.
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the bot:
   ```bash
   python -m bot.main
   ```

## Docker (Production)
1. Create `.env` based on `.env.example`.
2. Build and start:
   ```bash
   docker compose up -d --build
   ```
3. View logs:
   ```bash
   docker compose logs -f bot
   ```

## Update
```bash
git pull
docker compose up -d --build
```

## Backup
```bash
docker exec -t $(docker compose ps -q db) pg_dump -U namoz namoz > backup.sql
```
