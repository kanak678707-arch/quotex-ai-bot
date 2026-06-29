import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive

# টোকেন লোড
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# স্টার্ট কমান্ড চেক
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 হ্যালো! আমি সচল আছি। আপনার কোটেক্স চার্টের স্ক্রিনশটটি পাঠান।")

# ফটো হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    try:
        # মেসেজ পাওয়ার সাথে সাথে রেসপন্স করা নিশ্চিত করা
        status_msg = bot.reply_to(message, "📊 চার্ট পাওয়া গেছে। এআই বিশ্লেষণ শুরু করছে... অনুগ্রহ করে ২০ সেকেন্ড অপেক্ষা করুন।")
        
        # ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_chart.jpg"
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        # জেমিনি প্রম্পট সেটআপ
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        image = Image.open(image_path)
        
        prompt = """
        You are an elite Smart Money Concepts (SMC) and Price Action Trading AI.
        Analyze this candlestick chart screenshot very carefully.
        Identify current trend, support/resistance, and predict the next 1-minute candle (UP or DOWN).
        Provide output in a nice structured format with emojis. Include Asset Pair, Signal, Trend, Confidence Level, and a brief technical logic.
        """
        
        # এপিআই কল
        response = model.generate_content([prompt, image])
        
        # পুরানো স্ট্যাটাস মেসেজটি আপডেট বা ডিলিট করে ফাইনাল রেজাল্ট দেওয়া
        bot.edit_message_text(response.text, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
        
        # ফাইল রিমুভ
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        # কোনো ভুল হলে বট নিজেই চ্যাটে এরর লিখে দেবে
        bot.send_message(message.chat.id, f"❌ একটি ইন্টারনাল এরর হয়েছে:\n`{str(e)}`", parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    print("Bot is polling successfully...")
    # পোলিং গ্যাপ এবং টাইমআউট ফিক্স করা হলো যাতে রেন্ডারে আটকে না যায়
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
