from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="IoT Alert System")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Pydantic model for alert
class Alert(BaseModel):
    message: str

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Initialize database table on startup
def init_db():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# Initialize database on startup
init_db()

# Send Telegram message
async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Telegram error: {e}")
            raise

# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "IoT Alert System API",
        "endpoints": {
            "POST /alert": "Send an alert message",
            "GET /alerts": "Get all alerts",
            "GET /health": "Health check"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    db_status = "connected"
    conn = get_db_connection()
    if conn:
        conn.close()
    else:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

# Create alert endpoint
@app.post("/alert")
async def create_alert(alert: Alert):
    try:
        # Save to database
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alerts (message, created_at) VALUES (%s, %s) RETURNING id",
            (alert.message, datetime.now())
        )
        alert_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send Telegram notification
        telegram_message = f"🚨 <b>New Alert</b>\n\n{alert.message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await send_telegram_message(telegram_message)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": "Alert sent successfully",
            "telegram_sent": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Get all alerts
@app.get("/alerts")
async def get_alerts():
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50")
        alerts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
