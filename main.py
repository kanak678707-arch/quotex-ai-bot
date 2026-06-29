import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive
import time

# টেলিগ্রাম টোকেন লোড
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ৩টি জেমিনি এপিআই কি-এর লিস্ট তৈরি
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
            print(f"Key {index + 1} failed. Retrying next...")
            last_error = e
            time.sleep(1)
            continue
    raise last_error

# স্টার্ট কমান্ড
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "⚡ ১-মিনিট অ্যাগ্রেসিভ স্ক্যাল্পিং মোড চালু হয়েছে! কোটেক্স চার্টের স্ক্রিনশট পাঠান।")

# ফটো হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    try:
        status_msg = bot.reply_to(message, "⚡ স্ক্যাল্পিং মোড: ক্যান্ডেল ও ইন্ডিকেটর স্ক্যান করা হচ্ছে...")
        
        # ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_chart.jpg"
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        image = Image.open(image_path)
        
        # অ্যাগ্রেসিভ স্ক্যাল্পিং প্রম্পট (No Trade অপশন তুলে দেওয়া হলো)
        prompt = """
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
        
        # এপিআই কল
        response = generate_content_with_retry(prompt, image)
        ai_text = response.text
        
        # আউটপুট প্রসেস
        lines = ai_text.split('\n')
        asset = "N/A"
        pattern = "None"
        volume_status = "Normal"
        rsi = "Neutral"
        macd = "Neutral"
        signal = "N/A"
        confidence = "N/A"
        logic = ""
        
        capture_logic = False
        for line in lines:
            if "Asset Pair:" in line:
                asset = line.replace("Asset Pair:", "").strip()
            elif "Detected Pattern:" in line:
                pattern = line.replace("Detected Pattern:", "").strip()
            elif "Volume Status:" in line:
                volume_status = line.replace("Volume Status:", "").strip()
            elif "RSI Status:" in line:
                rsi = line.replace("RSI Status:", "").strip()
            elif "MACD Status:" in line:
                macd = line.replace("MACD Status:", "").strip()
            elif "Signal:" in line:
                signal = line.replace("Signal:", "").strip().upper()
            elif "Confidence Level:" in line:
                confidence = line.replace("Confidence Level:", "").strip()
            elif "Technical Logic:" in line:
                logic = line.replace("Technical Logic:", "").strip()
                capture_logic = True
            elif capture_logic:
                if line.strip():
                    logic += " " + line.strip()

        # গোল বাতি কাস্টমাইজেশন (অ্যাগ্রেসিভ ফিল্টার)
        if "UP" in signal:
            signal_output = "UP 🟢"
        else:
            signal_output = "DOWN 🔴"

        # ফাইনাল আউটপুট সাজানো
        final_message = (
            f"<b>Asset Pair:</b> {asset}\n"
            f"<b>Candle Pattern:</b> {pattern}\n"
            f"<b>Volume Status:</b> {volume_status}\n"
            f"<b>RSI Status:</b> {rsi}\n"
            f"<b>MACD Status:</b> {macd}\n"
            f"<b>Signal:</b> {signal_output}\n"
            f"<b>Confidence Level:</b> {confidence}\n\n"
            f"<b>Technical Logic (Tap to View):</b>\n"
            f"<tg-spoiler>{logic if logic else 'Analyzing quick scalping momentum.'}</tg-spoiler>"
        )
        
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ সাময়িক ত্রুটি হয়েছে, আবার চেষ্টা করুন।\n*(Error: {str(e)})*")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
