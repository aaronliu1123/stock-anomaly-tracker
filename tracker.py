import os
import requests
import yfinance as ticker_data

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TICKER = "NVDA"               # Stock ticker to monitor (e.g., TSLA, AAPL, SMMT)
VOLUME_THRESHOLD = 0.01        # Alert if volume is 3x the 20-minute rolling average
PRICE_PCT_THRESHOLD = 0.015   # Alert if price swings more than 1.5% in 1 minute

def send_telegram_alert(alert_body):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID variables.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": alert_body,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("📱 Alert pushed to Telegram successfully!")
        else:
            print(f"⚠️ Telegram API returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to transmit Telegram payload: {e}")

print(f"⏱️ Scanning {TICKER} intraday candle metrics...")
try:
    stock = ticker_data.Ticker(TICKER)
    df = stock.history(period="1d", interval="1m")

    if len(df) < 21:
        print("Insufficient trading bars generated for today yet.")
    else:
        past_window = df.tail(22).iloc[:-2]   # 20-minute baseline, excluding the last 2 rows
        current_candle = df.iloc[-2]          # the last FULLY CLOSED minute, not the live one

        avg_volume = past_window['Volume'].mean()
        current_volume = current_candle['Volume']

        minute_open = current_candle['Open']
        minute_close = current_candle['Close']
        price_pct_change = abs((minute_close - minute_open) / minute_open)

        vol_spike = current_volume > (avg_volume * VOLUME_THRESHOLD)
        price_spike = price_pct_change >= PRICE_PCT_THRESHOLD

        print(f"DEBUG: avg_volume={avg_volume}, current_volume={current_volume}, threshold_line={avg_volume * VOLUME_THRESHOLD}, vol_spike={vol_spike}")
        print(f"DEBUG: price_pct_change={price_pct_change:.4%}, price_spike={price_spike}")

        if vol_spike or price_spike:
            msg = f"🚨 *{TICKER} INTRADAY ANOMALY* 🚨\n\n"
            if vol_spike:
                msg += f"• *Volume Spike:* {int(current_volume):,} shares ({VOLUME_THRESHOLD}x avg)\n"
            if price_spike:
                msg += f"• *Price Shock:* moved {price_pct_change:.2%} in 60s\n"
            msg += f"• *Current Price:* ${minute_close:.2f}"

            send_telegram_alert(msg)
        else:
            print("No anomaly detected this check.")

except Exception as error:
    print(f"Market monitoring status: {error}")









