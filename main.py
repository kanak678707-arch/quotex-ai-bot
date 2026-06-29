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
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content([prompt, image])
            return response
        except Exception as e:
            print(f"Key {index + 1} failed, trying next...")
            last_error = e
            continue
    raise last_error

# প্রম্পট ছোট করা হয়েছে যাতে জেমিনি দ্রুত রেসপন্স করে
FAST_PROMPT = """
You are a 1-minute binary options sniper. Analyze this chart immediately.
CRITICAL: You must decide the NEXT candle direction right now. No neutral advice.

Provide the response exactly in this strict short format:
SIGNAL: [UP or DOWN]
CONFIDENCE: [Strict %]
PAIR: [Pair name]
LOGIC: [1 short sentence reason]
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "⚡ ১০-সেকেন্ড আল্ট্রা-ফাস্ট স্ক্যাল্পিং মোড একটিভ! চার্টের স্ক্রিনশট পাঠান।")

@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    image_path = "temp_chart.jpg"
    optimized_path = "fast_chart.jpg"
    try:
        # ১.১ সেকেন্ডে প্রথম রেসপন্স (ইউজারকে রেডি করা)
        status_msg = bot.reply_to(message, "⚡ স্নাইপার একটিভ... সিগন্যাল রেডি হচ্ছে...")
        
        # ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        # ছবির কোয়ালিটি ও সাইজ চরম লেভেলে ছোট করা (যাতে গুগলের কাছে ১ সেকেন্ডে আপলোড হয়)
        img = Image.open(image_path)
        img = img.resize((800, 450)) # আরও ছোট রেজোলিউশন (সুপার ফাস্ট)
        img.save(optimized_path, "JPEG", quality=60) # কোয়ালিটি ৬০% করায় ফাইলের সাইজ একদম হালকা হয়ে যাবে
        
        optimized_image = Image.open(optimized_path)
        
        # জেমিনি থেকে ফাস্ট ডেটা নেওয়া (গড়ে ৪-৫ সেকেন্ড লাগবে)
        response = generate_content_with_retry(FAST_PROMPT, optimized_image)
        ai_text = response.text
        
        # দ্রুত সিগন্যাল ফিল্টার করা
        lines = ai_text.split('\n')
        signal_direction = "UP"  # Default
        confidence = "80%"
        pair = "Crypto/OTC"
        logic = "Trend Momentum Shift"
        
        for line in lines:
            if "SIGNAL:" in line: signal_direction = line.replace("SIGNAL:", "").strip().upper()
            elif "CONFIDENCE:" in line: confidence = line.replace("CONFIDENCE:", "").strip()
            elif "PAIR:" in line: pair = line.replace("PAIR:", "").strip()
            elif "LOGIC:" in line: logic = line.replace("LOGIC:", "").strip()

        # ২. সিগন্যাল আইকন ঠিক করা
        if "UP" in signal_direction:
            signal_output = "🚨 SNIPER SIGNAL: UP 🟢🟢🟢"
        else:
            signal_output = "🚨 SNIPER SIGNAL: DOWN 🔴🔴🔴"

        # ৩. ঠিক ৫-৭ সেকেন্ডের মাথায় মেইন সিগন্যাল পাঠিয়ে দেওয়া (যা আপনি সাথে সাথে স্ক্রিনে দেখতে পাবেন)
        fast_message = (
            f"<b>{signal_output}</b>\n"
            f"<b>Confidence:</b> {confidence}\n"
            f"<b>Pair:</b> {pair}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <i>Technical details loading in 3 seconds...</i>"
        )
        bot.edit_message_text(fast_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
        # ৪. আপনি যখন এন্ট্রি নিচ্ছেন, তখন ব্যাকঅ্যান্ডে মেসেজটি আপডেট হয়ে পুরো লজিক বসে যাবে
        time.sleep(2) # সামান্য একটু গ্যাপ দিয়ে লজিকটা পুশ করা
        final_message = (
            f"<b>{signal_output}</b>\n"
            f"<b>Confidence:</b> {confidence}\n"
            f"<b>Pair:</b> {pair}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>🎯 Technical Logic:</b>\n"
            f"<tg-spoiler>{logic}</tg-spoiler>"
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
