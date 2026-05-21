from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv
import psycopg2
from typing import Optional

load_dotenv()

app = FastAPI(title="IoT Alert System")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

# Alert model
class Alert(BaseModel):
    error_type: str
    location: str
    severity: str  # low, medium, high, critical
    message: str
    device_id: Optional[str] = None
    additional_data: Optional[dict] = None

# Database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Send message to Telegram
async def send_telegram_alert(alert: Alert):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not configured")
        return False
    
    # Format message
    message = f"""
🚨 *ALERT NOTIFICATION*

📍 *Location:* {alert.location}
⚠️ *Error Type:* {alert.error_type}
🔴 *Severity:* {alert.severity.upper()}
💬 *Message:* {alert.message}
"""
    
    if alert.device_id:
        message += f"🔧 *Device ID:* {alert.device_id}\n"
    
    message += f"\n⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            })
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# Store alert in database
def store_alert(alert: Alert):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts (error_type, location, severity, message, device_id, additional_data, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            alert.error_type,
            alert.location,
            alert.severity,
            alert.message,
            alert.device_id,
            str(alert.additional_data) if alert.additional_data else None,
            datetime.now()
        ))
        
        alert_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return alert_id
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "IoT Alert System",
        "endpoints": {
            "POST /alert": "Send new alert",
            "GET /alerts": "Get all alerts",
            "GET /health": "Health check"
        }
    }

@app.post("/alert")
async def create_alert(alert: Alert):
    """
    Receive alert from frontend and forward to Telegram
    """
    try:
        # Store in database
        alert_id = store_alert(alert)
        
        # Send to Telegram
        telegram_sent = await send_telegram_alert(alert)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "telegram_sent": telegram_sent,
            "message": "Alert processed successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
def get_alerts(limit: int = 50):
    """
    Get recent alerts from database
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, error_type, location, severity, message, device_id, created_at
            FROM alerts
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                "id": row[0],
                "error_type": row[1],
                "location": row[2],
                "severity": row[3],
                "message": row[4],
                "device_id": row[5],
                "created_at": row[6].isoformat() if row[6] else None
            })
        
        cursor.close()
        conn.close()
        
        return {"alerts": alerts, "count": len(alerts)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
