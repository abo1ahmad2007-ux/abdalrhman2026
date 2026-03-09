import os
import sqlite3
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. إعداد نظام Flask للحفاظ على اتصال السيرفر
app = Flask('')

@app.route('/')
def home():
    return "بوت الإدارة الذاتية يعمل بنجاح!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. إعداد قاعدة البيانات لحفظ الأزرار للأبد
def init_db():
    conn = sqlite3.connect('buttons.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS buttons (name TEXT PRIMARY KEY, url TEXT)''')
    conn.commit()
    conn.close()

def add_button_to_db(name, url):
    conn = sqlite3.connect('buttons.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO buttons VALUES (?, ?)", (name, url))
    conn.commit()
    conn.close()

def get_all_buttons():
    conn = sqlite3.connect('buttons.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buttons")
    data = cursor.fetchall()
    conn.close()
    return data

# 3. إعدادات الأدمن (تم وضع ID الخاص بك هنا)
ADMIN_ID = 8560721192  

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons_data = get_all_buttons()
    keyboard = []
    for name, url in buttons_data:
        keyboard.append([InlineKeyboardButton(name, url=url)])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    msg = "مرحباً بك! اختر من الخدمات المتوفرة أدناه:" if keyboard else "مرحباً! لا توجد أزرار مضافة حالياً."
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🛠 **لوحة تحكم المدير**\n\n"
        "لإضافة زر جديد، أرسل رسالة بالصيغة التالية:\n"
        "`إضافة اسم_الزر رابط_الزر`\n\n"
        "مثال: `إضافة قناتنا https://t.me/example`"
    )

async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    text = update.message.text
    if text.startswith("إضافة"):
        try:
            parts = text.split(" ", 2)
            btn_name = parts[1]
            btn_url = parts[2]
            add_button_to_db(btn_name, btn_url)
            await update.message.reply_text(f"✅ تم الحفظ بنجاح! الزر '{btn_name}' متاح الآن للجميع.")
        except:
            await update.message.reply_text("❌ خطأ! تأكد من ترك مسافة بين 'إضافة' والاسم والرابط.")

def main():
    TOKEN = os.environ.get('BOT_TOKEN')
    init_db()
    keep_alive()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_commands))
    
    application.run_polling()

if __name__ == '__main__':
    main()
