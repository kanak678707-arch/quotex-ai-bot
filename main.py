import os
import telebot
import google.generativeai as genai
from PIL import Image
from keep_alive import keep_alive  # আমাদের তৈরি সার্ভার ইম্পোর্ট করলাম

# এপিআই কি সেটআপ (Render-এর Environment Variable থেকে আসবে)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# ফটো হ্যান্ডলার (টেলিগ্রামে চার্টের ছবি আসলে এই ফাংশন কাজ করবে)
@bot.message_handler(content_types=['photo'])
def handle_chart(message):
    try:
        bot.reply_to(message, "📊 চার্ট বিশ্লেষণ করা হচ্ছে... অনুগ্রহ করে ১৫-২০ সেকেন্ড অপেক্ষা করুন।")
        
        # ১. টেলিগ্রাম থেকে ছবি ডাউনলোড
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_chart.jpg"
        with open(image_path, 'wb') as f:
            f.write(downloaded_file)
            
        # ২. জেমিনি মডেল সেটআপ এবং অ্যাডভান্সড ট্রেডিং প্রম্পট
        model = genai.GenerativeModel('gemini-1.5-flash')
        image = Image.open(image_path)
        
        # এখানে আমরা বটকে SMC ও অন্যান্য লজিক শিখিয়ে দিচ্ছি
        prompt = """
        You are an elite Smart Money Concepts (SMC) and Price Action Trading AI.
        Analyze this 1-minute candlestick chart screenshot very carefully.
        
        Look for:
        1. Current Market Structure (CHoCH or BOS).
        2. Unmitigated Order Blocks (OB) and Fair Value Gaps (FVG).
        3. Liquidity sweeps (Buy-side/Sell-side liquidity).
        4. Support/Resistance zones and potential OTC manipulations.

        Provide the output strictly in this beautiful format (Use emojis for telegram):
        
        📊 **SWEETEX AI ANALYSIS** 📊
        ━━━━━━━━━━━━━━━━━━
        🪙 **Asset Pair:** [Identify pair if visible, else auto]
        📈 **Signal:** [UP / DOWN / NEUTRAL]
        📉 **Trend:** [e.g., Bearish with short-term consolidation]
        🎯 **Confidence Level:** [0% to 100%]
        
        🧠 **TECHNICAL LOGIC:**
        • [Explain why you gave UP or DOWN based on SMC/Order Blocks/Candlestick patterns]
        • [Mention Support/Resistance levels or FVG filled]
        
        ⚠️ *Note: Always use 1-Step MTG if the first candle fails.*
        """
        
        # ৩. জেমিনি থেকে রেসপন্স নেওয়া
        response = model.generate_content([prompt, image])
        
        # ৪. ইউজারকে রেজাল্ট পাঠানো
        bot.reply_to(message, response.text, parse_mode="Markdown")
        
        # সাময়িক ফাইলটি ডিলিট করা
        os.remove(image_path)
        
    except Exception as e:
        bot.reply_to(message, f"❌ দুঃখিত, একটি সমস্যা হয়েছে: {str(e)}")

# বট এবং ওয়েব সার্ভার একসাথে চালু করা
if __name__ == "__main__":
    keep_alive()  # ব্যাকগ্রাউন্ডে ওয়েব সার্ভার চালু হবে
    print("Bot is polling...")
    bot.infinity_polling()