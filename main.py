import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive

# টোকen লোড
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

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
            
        # অল্টারনেটিভ লেটেস্ট মডেল ট্রাই করুন
        model = genai.GenerativeModel('gemini-2.5-flash') 
        image = Image.open(image_path)
        
        # প্রম্পটে কড়া ইন্সট্রাকশন দেওয়া হয়েছে ফরম্যাটের জন্য
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
        
        # এপিআই কল
        response = model.generate_content([prompt, image])
        ai_text = response.text
        
        # এআই-এর আউটপুট প্রসেস করে কাস্টম ইমোজি এবং স্পয়লার অ্যাড করা
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

        # সিগন্যাল অনুযায়ী আপনার পছন্দের গোল বাতি ইমোজি সেট করা
        if "UP" in signal:
            signal_output = "UP 🟢"
        elif "DOWN" in signal:
            signal_output = "DOWN 🔴"
        else:
            signal_output = signal

        # HTML ফরম্যাটে সুন্দর করে সাজানো (সিমোর বা স্পয়লার ইফেক্টসহ)
        final_message = (
            f"<b>Asset Pair:</b> {asset}\n"
            f"<b>Signal:</b> {signal_output}\n"
            f"<b>Trend:</b> {trend}\n"
            f"<b>Confidence Level:</b> {confidence}\n\n"
            f"<b>Technical Logic (Tap to View):</b>\n"
            f"<tg-spoiler>{logic if logic else 'Analyzing structure and liquidity zones.'}</tg-spoiler>"
        )
        
        # ফাইনাল মেসেজটি HTML মোডে পাঠানো
        bot.edit_message_text(final_message, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ একটি ইন্টারনাল এরর হয়েছে:\n{str(e)}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
