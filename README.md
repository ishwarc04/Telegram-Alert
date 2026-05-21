# IoT Alert System 🚨

A FastAPI-based alert system that sends notifications to Telegram and stores them in PostgreSQL.

## Features

- 📡 REST API for sending alerts
- 💬 Instant Telegram notifications
- 🗄️ PostgreSQL database storage
- ☁️ Ready for Render deployment

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /alert` - Send an alert
- `GET /alerts` - Get all alerts

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
DATABASE_URL=your_postgresql_url
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

3. Run the server:
```bash
uvicorn main:app --reload
```

## Deployment on Render

1. Push to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Add environment variables:
   - `DATABASE_URL`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Deploy!

## Usage Example

```bash
curl -X POST https://your-app.onrender.com/alert \
  -H "Content-Type: application/json" \
  -d '{"message": "Temperature alert: 35°C"}'
```

## Tech Stack

- FastAPI
- PostgreSQL
- Telegram Bot API
- Render (hosting)
