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
    bot.reply_to(message, "👋 আল্ট্রা ভলিউম ও ইন্ডিকেটর মোড একটিভ! চার্টে RSI, MACD এবং Volume On করে স্ক্রিনশট পাঠান।")

# ফটো হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    try:
        status_msg = bot.reply_to(message, "📊 ক্যান্ডেল, ইন্ডিকেটর এবং লাইভ ভলিউম স্ক্যান করা হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।")
        
        # ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_chart.jpg"
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        image = Image.open(image_path)
        
        # ভলিউম রিড করার জন্য প্রম্পটে নতুন নিয়ম যোগ করা হলো
        prompt = """
        You are an advanced Institutional Trading Expert specializing in Volume Spread Analysis (VSA), Candlestick Patterns, and Technical Indicators (RSI, MACD) for 1-minute live Forex/Binary markets.
        Analyze this screenshot with flawless precision:
        
        1. Volume Analysis (VSA): Look at the volume bars at the bottom of the chart. Compare the latest candle's volume bar with the previous 5 volume bars. Detect if it is High Volume (validating the move) or Low Volume (indicating an anomaly or fake breakout/exhaustion).
        2. Candlestick Pattern: Identify high-probability setups (Hammer, Shooting Star, Engulfing, etc.) and confirm it with the corresponding volume bar. High volume on a reversal candle means institutional confirmation.
        3. Indicator Synergy: Check RSI (Overbought/Oversold/Divergence) and MACD crossover.
        4. Strict Confluence Filter: 
           - Give UP or DOWN only if Price Action, Volume (VSA), RSI, and MACD all align in the same direction with high volume support.
           - If volume is declining during a breakout, or indicators conflict, you MUST output "NO TRADE".
        
        You MUST provide the response exactly in this strict English format below without any extra markdown symbols outside:
        
        Asset Pair: [Pair name]
        Detected Pattern: [Pattern name or 'None']
        Volume Status: [High Volume Confirmation, Low Volume/Fakeout Alert, or Decreasing Volume]
        RSI Status: [Overbought, Oversold, Neutral, or Divergence]
        MACD Status: [Bullish Crossover, Bearish Crossover, or No Crossover]
        Signal: [UP, DOWN, or NO TRADE]
        Confidence Level: [Strict % based on VSA + Indicator confirmation]
        Technical Logic: [Explain exactly how the volume bars and candlestick price action confirm or reject the current market momentum in 2-3 precise sentences]
        """
        
        # এপিআই কল
        response = generate_content_with_retry(prompt, image)
        ai_text = response.text
        
        # আউটপুট প্রসেস
        lines = ai_text.split('\n')
        asset = "N/A"
        pattern = "None"
        volume_status = "Neutral"
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

        # গোল বাতি কাস্টমাইজেশন
        if "UP" in signal and "NO" not in signal:
            signal_output = "UP 🟢"
        elif "DOWN" in signal:
            signal_output = "DOWN 🔴"
        else:
            signal_output = "⚠️ NO TRADE (Volume/Indicator Conflict) ⚠️"

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
            f"<tg-spoiler>{logic if logic else 'Analyzing volume bars integration.'}</tg-spoiler>"
        )
        
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ সাময়িক ত্রুটি হয়েছে, আবার চেষ্টা করুন।\n*(Error: {str(e)})*")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
