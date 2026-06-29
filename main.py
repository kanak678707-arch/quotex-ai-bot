import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive
import time

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ৩টি ফ্রি কি রোটেশন
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

# 🎯 আপনার সেই চমৎকার ও নিখুঁত বড় প্রম্পটটিই এখানে রাখা হলো
SCALPER_PROMPT = """
You are an Elite AI High-Frequency Quantitative Scalper, specialized in 1-minute binary options contract analysis for Quotex. 
Your core directive is to decode the provided chart screenshot and deliver a high-probability sniper forecast for the immediate NEXT 1-MINUTE CANDLE.

Absolute Operational Command: You are FORBIDDEN from being neutral or outputting "NO TRADE". You must mathematically weigh the buyers' vs. sellers' short-term dominance and commit to either UP or DOWN.

Instantly run the chart through these 4 Proprietary Institutional Frameworks:
1. SMART MONEY REJECTION & BODY-TO-WICK RATIO: Scan the last 3 candles. Analyze the rejection tails. A long lower wick at a Key Support Zone proves Institutional Liquidity Sweep (Bullish Rejection) -> Filter DOWN, force UP. A long upper wick at a Resistance Level proves Supply absorption (Bearish Rejection) -> Filter UP, force DOWN.
2. SNR BREAKOUT VS. FAKEOUT (S&R): Determine if the current price candle is breaking a major horizontal support/resistance level or forming a fakeout. If a candle closes robustly BEYOND a level with surging volume -> follow the Breakout. If it closes as a weak pinbar pushing back inside the zone -> trade the Reverse.
3. RSI BOUNDARY EXHAUSTION: Locate the RSI line at the bottom. If RSI <= 28 (Extreme Oversold Exhaustion), do NOT hunt for DOWN; your algorithm must heavily bias toward an UP reversal. If RSI >= 72 (Extreme Overbought Exhaustion), do NOT hunt for UP; your algorithm must heavily bias toward a DOWN reversal.
4. MACD & VOLUME CONFLUENCE TIER: Cross-reference price velocity with the bottom Volume Histogram. High-volume candles validating MACD crossovers signify institutional participation.

You MUST provide the response exactly in this strict English format below without any extra markdown symbols outside:

Asset Pair: [Pair name, e.g., EUR/USD or USD/JPY]
Detected Pattern: [SMC Liquidity Sweep / SNR Breakout / False Breakout / Momentum Continuation]
Volume Status: [Climax High / Dying Low / Neutral]
RSI Status: [Overbought Exhaustion (No UP) / Oversold Exhaustion (No DOWN) / Zone Trading]
MACD Status: [Bullish Divergence / Bearish Crossover / Trapped Neutral]
Signal: [UP or DOWN]
Confidence Level: [Strict % quantified from your 4-tier strategy match]
Technical Logic: [Explain the precise mathematical/SMC trigger driving this sniper shot in 1-2 ultra-short sentences]
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "⚡ আপনার পারফেক্ট স্নাইপার মোড একটিভ! চার্টের স্ক্রিনশট পাঠান (৪০ সেকেন্ডে)।")

@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    image_path = "temp_chart.jpg"
    optimized_path = "fast_chart.jpg"
    try:
        status_msg = bot.reply_to(message, "⚡ স্নাইপার শট রেডি হচ্ছে...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        # ইমেজ সাইজ সুপার লাইট করা (স্পিড বুস্টের জন্য)
        img = Image.open(image_path)
        img = img.resize((900, 506)) 
        img.save(optimized_path, "JPEG", quality=65)
        
        optimized_image = Image.open(optimized_path)
        
        # জেমিনি এপিআই কল
        response = generate_content_with_retry(SCALPER_PROMPT, optimized_image)
        ai_text = response.text
        
        # ডাটা প্রসেসিং
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

        # 🔥 ১ম ধাপ: ৫-৭ সেকেন্ডের মাথায় চোখের পলকে শুধু মেইন সিগন্যালটা স্ক্রিনে চলে আসবে
        fast_message = (
            f"🎯 <b>SIGNAL: {signal_output}</b>\n"
            f"🔥 <b>Confidence:</b> {confidence}\n"
            f"📊 <b>Pair:</b> {asset}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <i>Analyzing indicators & logic...</i>"
        )
        bot.edit_message_text(fast_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
        # 🤝 ২য় ধাপ: আপনি যখন কোটেক্সে এন্ট্রি নিচ্ছেন, ব্যাকএন্ডে ২ সেকেন্ড পর পুরো লজিক মেসেজে যোগ হয়ে যাবে
        time.sleep(1.5)
        final_message = (
            f"🎯 <b>SIGNAL: {signal_output}</b>\n"
            f"🔥 <b>Confidence:</b> {confidence}\n"
            f"📊 <b>Pair:</b> {asset}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Pattern:</b> {pattern}\n"
            f"<b>RSI:</b> {rsi} | <b>MACD:</b> {macd}\n"
            f"<b>Volume:</b> {volume_status}\n\n"
            f"<b>💡 Sniper Technical Logic:</b>\n"
            f"<tg-spoiler>{logic if logic else 'Matched with multiple indicator trend.'}</tg-spoiler>"
        )
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ সার্ভার ব্যস্ত। অনুগ্রহ করে ৫ সেকেন্ড পর আবার চেষ্টা করুন।")
    finally:
        if os.path.exists(image_path): os.remove(image_path)
        if os.path.exists(optimized_path): os.remove(optimized_path)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
