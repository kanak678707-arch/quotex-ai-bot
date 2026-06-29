import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive
import time

# টেলিগ্রাম টোকেন লোড
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ৩টি জেমিনি এপিআই কি-এর লিস্ট তৈরি (ফোল্ডার সিস্টেম)
API_KEYS = [
    os.environ.get('GEMINI_API_KEY_1'),
    os.environ.get('GEMINI_API_KEY_2'),
    os.environ.get('GEMINI_API_KEY_3')
]

# ফিল্টার করে নেওয়া যাতে কোনো কি খালি থাকলে কোড ক্র্যাশ না করে
API_KEYS = [key for key in API_KEYS if key]

def generate_content_with_retry(prompt, image):
    """৩টি কি-এর মধ্যে অটোমেটিক সুইচ করার মূল ফাংশন"""
    last_error = None
    
    for index, key in enumerate(API_KEYS):
        try:
            print(f"Trying Gemini API Key {index + 1}...")
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash') 
            
            # এপিআই কল
            response = model.generate_content([prompt, image])
            print(f"Success using API Key {index + 1}!")
            return response
        except Exception as e:
            print(f"API Key {index + 1} failed. Error: {str(e)}")
            last_error = e
            # একটি কি ফেল করলে পরের কি-তে যাওয়ার আগে ১ সেকেন্ড ওয়েট করবে
            time.sleep(1)
            continue
            
    # যদি ৩টি কি-র একটিও কাজ না করে, তবেই কেবল ফাইনাল এরর থ্রো করবে
    raise last_error

# স্টার্ট কমান্ড
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 হ্যালো! আপনার কোটেক্স চার্টের স্ক্রিনশটটি পাঠান।")

# ফটো হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    try:
        status_msg = bot.reply_to(message, "📊 চার্ট পাওয়া গেছে। এআই বিশ্লেষণ শুরু করছে... অনুগ্রহ করে অপেক্ষা করুন।")
        
        # ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_chart.jpg"
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        image = Image.open(image_path)
        
        prompt = """
        You are an elite Smart Money Concepts (SMC) and Price Action Trading AI.
        Analyze this candlestick chart screenshot very carefully.
        Predict the next 1-minute candle (UP or DOWN).
        
        You MUST provide the response exactly in this English format below. Do not change the labels or add any extra text or stars outside.
        
        Asset Pair: [Write pair name here]
        Signal: [Write UP or DOWN here]
        Trend: [Write Trend here]
        Confidence Level: [Write % here]
        Technical Logic: [Write the technical logic analysis here in 2-3 sentences]
        """
        
        # অটো-রোটেশন ফাংশন কল করা হলো
        response = generate_content_with_retry(prompt, image)

        ai_text = response.text
        
        # এআই-এর আউটপুট প্রসেস করা
        lines = ai_text.split('\n')
        asset = "N/A"
        signal = "N/A"
        trend = "N/A"
        confidence = "N/A"
        logic = ""
        
        capture_logic = False
        for line in lines:
            if "Asset Pair:" in line:
                asset = line.replace("Asset Pair:", "").strip()
            elif "Signal:" in line:
                signal = line.replace("Signal:", "").strip().upper()
            elif "Trend:" in line:
                trend = line.replace("Trend:", "").strip()
            elif "Confidence Level:" in line:
                confidence = line.replace("Confidence Level:", "").strip()
            elif "Technical Logic:" in line:
                logic = line.replace("Technical Logic:", "").strip()
                capture_logic = True
            elif capture_logic:
                if line.strip():
                    logic += " " + line.strip()

        if "UP" in signal:
            signal_output = "UP 🟢"
        elif "DOWN" in signal:
            signal_output = "DOWN 🔴"
        else:
            signal_output = signal

        final_message = (
            f"<b>Asset Pair:</b> {asset}\n"
            f"<b>Signal:</b> {signal_output}\n"
            f"<b>Trend:</b> {trend}\n"
            f"<b>Confidence Level:</b> {confidence}\n\n"
            f"<b>Technical Logic (Tap to View):</b>\n"
            f"<tg-spoiler>{logic if logic else 'Analyzing structure and liquidity zones.'}</tg-spoiler>"
        )
        
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ দুঃখিত, এআই সার্ভার বর্তমানে ওভারলোডেড। অনুগ্রহ করে ১৫ সেকেন্ড পর আবার চেষ্টা করুন।\n\n*(Error Details: {str(e)})*")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
