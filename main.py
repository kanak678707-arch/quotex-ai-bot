import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive
import time

# টেলিগ্রাম টোকেন লোড
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# জাস্ট ১টি ফ্রি জেমিনি এপিআই কি লোড হবে (কোনো টাকা লাগবে না)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# এগ্রেসিভ স্ক্যাল্পিং প্রম্পট (সবসময় UP/DOWN দিতে বাধ্য করবে)
SCALPER_PROMPT = """
You are a high-frequency Scalping Trader expert in 1-minute binary options. 
Analyze this chart screenshot instantly. You MUST give a clear prediction for the next 1-minute candle.

CRITICAL RULE: Do NOT say "NO TRADE". You are FORBIDDEN from giving neutral advice. You MUST pick either UP or DOWN based on whichever side has even a slight statistical advantage.

1. Look at the last 2-3 candles and their immediate momentum (Candlestick psychology).
2. Look at the RSI, MACD, and Volume trends at the bottom to determine the immediate direction.
3. Make a definitive choice: If buyers are even slightly stronger, give UP. If sellers are even slightly stronger, give DOWN.

You MUST provide the response exactly in this strict English format below without any extra markdown symbols outside:

Asset Pair: [Pair name]
Detected Pattern: [Pattern name or 'None']
Volume Status: [High/Low/Normal]
RSI Status: [Overbought/Oversold/Neutral]
MACD Status: [Bullish/Bearish/Neutral]
Signal: [UP or DOWN]
Confidence Level: [Strict % based on your short-term momentum calculation]
Technical Logic: [Explain the immediate 1-minute scalping reason in 1-2 short sentences]
"""

# স্টার্ট কমান্ড
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "⚡ ১-মিনিট ফ্রি স্ক্যাল্পিং মোড একটিভ! কোটেক্স চার্টের স্ক্রিনশট পাঠান।")

# ফটো হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    image_path = "temp_chart.jpg"
    try:
        status_msg = bot.reply_to(message, "⚡ ক্যান্ডেল ও ইন্ডিকেটর স্ক্যান করা হচ্ছে...")
        
        # ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        image = Image.open(image_path)
        
        # ফ্রি জেমিনি মডেল কল (১.৫ ফ্ল্যাশ ২0২6 সালেও সম্পূর্ণ ফ্রি ও ফাস্ট)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([SCALPER_PROMPT, image])
        ai_text = response.text
        
        # আউটপুট প্রসেস
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

        # ফাইনাল মেসেজ ফরম্যাট
        final_message = (
            f"<b>Asset Pair:</b> {asset}\n"
            f"<b>Candle Pattern:</b> {pattern}\n"
            f"<b>Volume Status:</b> {volume_status}\n"
            f"<b>RSI Status:</b> {rsi}\n"
            f"<b>MACD Status:</b> {macd}\n"
            f"<b>Signal:</b> {signal_output}\n"
            f"<b>Confidence Level:</b> {confidence}\n\n"
            f"<b>Technical Logic (Tap to View):</b>\n"
            f"<tg-spoiler>{logic if logic else 'Analyzing 1-minute momentum.'}</tg-spoiler>"
        )
        
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ এপিআই ওভারলোড হয়েছে। প্লিজ ৫ সেকেন্ড পর আবার ছবিটি পাঠান।")
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
