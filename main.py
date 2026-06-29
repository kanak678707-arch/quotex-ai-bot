import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive
import time

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ৩টি আলাদা ফ্রি এপিআই কি-এর লিস্ট
API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3')
]
API_KEYS = [key for key in API_KEYS if key]

def generate_content_with_retry(prompt, image):
    last_error = None
    for index, key in enumerate(API_KEYS):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([prompt, image])
            return response
        except Exception as e:
            print(f"Key {index + 1} failed, trying next...")
            last_error = e
            continue
    raise last_error

SCALPER_PROMPT = """
You are a World-Class High-Frequency Sniper Scalper Trader specializing in 1-minute Binary Options (Quotex).
Your goal is to analyze this chart screenshot and take a flawless 'Sniper Shot' for the NEXT 1-MINUTE CANDLE.

CRITICAL RULE: Do NOT say "NO TRADE" or give neutral/confusing advice. You MUST pick either UP or DOWN based on the absolute highest probability direction.

Apply these ULTRA-SNIPER STRATEGIES instantly:
1. CANDLESTICK PSYCHOLOGY & WICKS (SMC): Look at the last 2-3 candles. If the current running candle has a very long lower wick (tail) near a support level, it means strong rejection by buyers -> Filter DOWN signals, give UP. If it has a long upper wick near resistance, it means seller rejection -> Filter UP signals, give DOWN.
2. RSI EXHAUSTION FILTER: Check the RSI at the bottom. If RSI is below 30 (Oversold), the market is exhausted; you are STRICTLY FORBIDDEN from giving a DOWN signal. If RSI is above 70 (Overbought), you are STRICTLY FORBIDDEN from giving an UP signal.
3. MACD & VOLUME CONFLUENCE: Ensure the Volume bars and MACD crossovers match the candle momentum. True sniper entry requires at least 3 indicators/price action rules to align in the same direction.

You MUST provide the response exactly in this strict English format below without any extra markdown symbols outside:

Asset Pair: [Pair name, e.g., USD/JPY]
Detected Pattern: [SMC Rejection / Bullish Engulfing / Support Touch / None]
Volume Status: [High / Low / Normal]
RSI Status: [Overbought (No UP) / Oversold (No DOWN) / Neutral]
MACD Status: [Bullish / Bearish / Neutral]
Signal: [UP or DOWN]
Confidence Level: [Strict % based on how many sniper rules matched]
Technical Logic: [Explain the exact Sniper Shot reason based on Wicks, RSI, or Support/Resistance in 1-2 short sentences]
"""
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "⚡ আল্ট্রা-লাইট স্ক্যাল্পিং মোড চালু হয়েছে! ৩টি ভিন্ন ফ্রি কি এবং ইমেজ অপ্টিমাইজেশন একটিভ।")

@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    image_path = "temp_chart.jpg"
    optimized_path = "optimized_chart.jpg"
    try:
        status_msg = bot.reply_to(message, "⚡ ক্যান্ডেল ও ইন্ডিকেটর স্ক্যান করা হচ্ছে...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        # 🛠️ টোকেন বাঁচানোর ম্যাজিক ট্রিক: ছবি সাইজ ও কোয়ালিটি ছোট করা
        img = Image.open(image_path)
        img = img.resize((1024, 576)) # রেজোলিউশন কমানো হলো যাতে টোকেন কম কাটে
        img.save(optimized_path, "JPEG", quality=75) # কোয়ালিটি ৭৫% করায় সাইজ অনেক কমে যাবে
        
        optimized_image = Image.open(optimized_path)
        
        response = generate_content_with_retry(SCALPER_PROMPT, optimized_image)
        ai_text = response.text
        
        lines = ai_text.split('\n')
        asset, pattern, volume_status, rsi, macd, signal, confidence, logic = "N/A", "None", "Normal", "Neutral", "Neutral", "N/A", "N/A", ""
        
        capture_logic = False
        for line in lines:
            if "Asset Pair:" in line: asset = line.replace("Asset Pair:", "").strip()
            elif "Detected Pattern:" in line: pattern = line.replace("Detected Pattern:", "").strip()
            elif "Volume Status:" in line: volume_status = line.replace("Volume Status:", "").strip()
            elif "RSI Status:" in line: rsi = line.replace("RSI Status:", "").strip()
            elif "MACD Status:" in line: macd = line.replace("MACD Status:", "").strip()
            elif "Signal:" in line: signal = line.replace("Signal:", "").strip().upper()
            elif "Confidence Level:" in line: confidence = line.replace("Confidence Level:", "").strip()
            elif "Technical Logic:" in line:
                logic = line.replace("Technical Logic:", "").strip()
                capture_logic = True
            elif capture_logic and line.strip():
                logic += " " + line.strip()

        signal_output = "UP 🟢" if "UP" in signal else "DOWN 🔴"

        final_message = (
            f"<b>Asset Pair:</b> {asset}\n"
            f"<b>Candle Pattern:</b> {pattern}\n"
            f"<b>Volume Status:</b> {volume_status}\n"
            f"<b>RSI Status:</b> {rsi}\n"
            f"<b>MACD Status:</b> {macd}\n"
            f"<b>Signal:</b> {signal_output}\n"
            f"<b>Confidence Level:</b> {confidence}\n\n"
            f"<b>Technical Logic:</b>\n"
            f"<tg-spoiler>{logic if logic else 'Analyzing quick momentum.'}</tg-spoiler>"
        )
        
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ সবকটি ফ্রি সার্ভার এই মুহূর্তে ব্যস্ত। অনুগ্রহ করে ১০ সেকেন্ড পর আবার চেষ্টা করুন।")
    finally:
        if os.path.exists(image_path): os.remove(image_path)
        if os.path.exists(optimized_path): os.remove(optimized_path)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
