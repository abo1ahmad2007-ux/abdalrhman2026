import os
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# 1. استمرارية السيرفر
app = Flask('')
@app.route('/')
def home(): return "نظام Manybot المطور يعمل"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# 2. قاعدة البيانات
def init_db():
    conn = sqlite3.connect('manybot_style.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS content (name TEXT PRIMARY KEY, type TEXT, val TEXT, file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

ADMIN_ID = 8560721192 

# --- القائمة الرئيسية للمستخدمين ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('manybot_style.db')
    conn.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    btns = conn.execute("SELECT name FROM content").fetchall()
    conn.commit()
    conn.close()

    keyboard = []
    for i in range(0, len(btns), 2):
        row = [InlineKeyboardButton(btns[i][0], callback_data=f"show_{btns[i][0]}")]
        if i + 1 < len(btns): row.append(InlineKeyboardButton(btns[i+1][0], callback_data=f"show_{btns[i+1][0]}"))
        keyboard.append(row)

    msg = "🤖 **مرحباً بك في البوت!**\nاستخدم الأزرار أدناه لتصفح المحتوى:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message: await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

# --- لوحة التحكم (ستايل Manybot) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [
        [InlineKeyboardButton("➕ إنشاء أمر (زر) جديد", callback_data='adm_add')],
        [InlineKeyboardButton("🗑 حذف أمر موجود", callback_data='adm_del')],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data='adm_broadcast')]
    ]
    await update.message.reply_text("⚙️ **إعدادات البوت (Manybot Mode)**\nاختر ماذا تريد أن تفعل:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- معالجة الضغط على الأزرار ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("show_"):
        name = data.replace("show_", "")
        conn = sqlite3.connect('manybot_style.db')
        res = conn.execute("SELECT type, val, file_id FROM content WHERE name=?", (name,)).fetchone()
        conn.close()
        if res[0] == 'text': await query.message.reply_text(f"📌 {name}:\n\n{res[1]}")
        else: await query.message.reply_document(document=res[2], caption=f"📄 {name}")

    elif data == 'adm_add':
        context.user_data['action'] = 'waiting_name'
        await query.message.reply_text("ارسل الآن **اسم الزر** الذي تريد إنشاءه:")

    elif data == 'adm_del':
        conn = sqlite3.connect('manybot_style.db')
        btns = conn.execute("SELECT name FROM content").fetchall()
        conn.close()
        keyboard = [[InlineKeyboardButton(f"❌ {b[0]}", callback_data=f"confirm_del_{b[0]}")] for b in btns]
        await query.edit_message_text("اختر الزر المراد حذفه:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("confirm_del_"):
        name = data.replace("confirm_del_", "")
        conn = sqlite3.connect('manybot_style.db')
        conn.execute("DELETE FROM content WHERE name=?", (name,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم حذف الزر '{name}'")

# --- معالجة الإدخالات النصية والملفات ---
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    action = context.user_data.get('action')

    if action == 'waiting_name':
        context.user_data['new_btn_name'] = update.message.text
        context.user_data['action'] = 'waiting_content'
        await update.message.reply_text(f"تمام، الحين ارسل 'محتوى' الزر الجديد (نص، رابط، أو ملف PDF/صورة):")

    elif action == 'waiting_content':
        name = context.user_data['new_btn_name']
        conn = sqlite3.connect('manybot_style.db')
        
        if update.message.text:
            conn.execute("INSERT OR REPLACE INTO content VALUES (?, ?, ?, ?)", (name, 'text', update.message.text, None))
        elif update.message.document or update.message.photo:
            file_id = update.message.document.file_id if update.message.document else update.message.photo[-1].file_id
            conn.execute("INSERT OR REPLACE INTO content VALUES (?, ?, ?, ?)", (name, 'file', 'file', file_id))
        
        conn.commit()
        conn.close()
        context.user_data.clear()
        await update.message.reply_text(f"✅ مبروك! الزر '{name}' صار جاهز في القائمة.")

def main():
    TOKEN = os.environ.get('BOT_TOKEN')
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_input))
    application.run_polling()

if __name__ == '__main__': main()
