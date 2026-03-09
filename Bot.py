import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعداد نظام Flask لمنع السيرفر من النوم (Anti-Sleep)
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح في السحاب!"

def run():
    # Render يستخدم المنفذ 8080 بشكل افتراضي
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. إعدادات البوت الأساسية
# سيقوم الكود بقراءة التوكن من Environment Variables التي شرحناها
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أنا بوت الطلاب، أعمل الآن 24 ساعة من السيرفر.")

if __name__ == '__main__':
    # تشغيل سيرفر الويب في الخلفية
    keep_alive()
    
    # بناء وتشغيل البوت
    if TOKEN:
        application = ApplicationBuilder().token(TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        application.add_handler(start_handler)
        
        print("جاري تشغيل البوت...")
        application.run_polling()
    else:
        print("خطأ: لم يتم العثور على BOT_TOKEN في إعدادات السيرفر!")
