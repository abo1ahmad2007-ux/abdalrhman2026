import os
import sqlite3
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# 1. إعداد السيرفر (Flask)
app = Flask('')
@app.route('/')
def home(): return "بوت الطالب المطور يعمل!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# 2. إعداد قاعدة البيانات (لحفظ البيانات والملفات)
def init_db():
    conn = sqlite3.connect('student_bot.db')
    c = conn.cursor()
    # جدول الطلاب
    c.execute('''CREATE TABLE IF NOT EXISTS students (user_id INTEGER PRIMARY KEY, info TEXT)''')
    # جدول الأزرار والمحتوى (نص، ملف، صورة، رابط)
    c.execute('''CREATE TABLE IF NOT EXISTS content (btn_name TEXT PRIMARY KEY, type TEXT, value TEXT, file_id TEXT)''')
    conn.commit()
    conn.close()

# 3. إعدادات الأدمن (ID الخاص بك)
ADMIN_ID = 8560721192 

# --- دالة عرض القائمة الرئيسية ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('student_bot.db')
    buttons = conn.execute("SELECT btn_name FROM content").fetchall()
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton("📚 قسم التسجيل / البيانات", callback_data='reg_info')],
        [InlineKeyboardButton("📝 تقديم شكوى", callback_data='complaint')]
    ]
    # إضافة الأزرار التي صممها الأدمن تلقائياً
    custom_rows = [InlineKeyboardButton(b[0], callback_data=f"show_{b[0]}") for b in buttons]
    for i in range(0, len(custom_rows), 2): # ترتيب كل زرين في سطر
        keyboard.append(custom_rows[i:i+2])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("🎓 أهلاً بك في بوت الطالب. اختر القسم:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("🎓 اختر القسم المطلوب:", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

# 4. لوحة تحكم الأدمن (إضافة وتعديل)
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(
        "🛠 **لوحة تحكم الأدمن**\n\n"
        "1️⃣ **لإضافة نص أو رابط:**\n`إضافة اسم_الزر المحتوى`\n"
        "2️⃣ **لإضافة ملف (PDF، صورة، إلخ):**\nأرسل الملف مع كتابة كلمة `زر_ملف اسم_الزر` في الوصف (Caption)."
    )

# 5. معالجة الرسائل (نصوص وملفات)
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""
    caption = update.message.caption or ""

    if user_id == ADMIN_ID:
        # إضافة نص أو رابط
        if text.startswith("إضافة"):
            parts = text.split(" ", 2)
            name, val = parts[1], parts[2]
            conn = sqlite3.connect('student_bot.db')
            conn.execute("INSERT OR REPLACE INTO content VALUES (?, ?, ?, ?)", (name, "text", val, None))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"✅ تم إضافة زر نصي باسم: {name}")
            return

        # إضافة ملف (PDF، صورة، فيديو)
        if caption.startswith("زر_ملف"):
            btn_name = caption.replace("زر_ملف", "").strip()
            file_id = None
            f_type = "file"
            
            if update.message.document: file_id = update.message.document.file_id
            elif update.message.photo: file_id = update.message.photo[-1].file_id
            
            if file_id:
                conn = sqlite3.connect('student_bot.db')
                conn.execute("INSERT OR REPLACE INTO content VALUES (?, ?, ?, ?)", (btn_name, f_type, "ملف", file_id))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"✅ تم إنشاء زر ملف باسم: {btn_name}")
                return

# 6. التفاعل مع الأزرار
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("show_"):
        btn_name = data.replace("show_", "")
        conn = sqlite3.connect('student_bot.db')
        item = conn.execute("SELECT type, value, file_id FROM content WHERE btn_name=?", (btn_name,)).fetchone()
        conn.close()

        if item[0] == "text":
            await query.message.reply_text(f"📌 {btn_name}:\n\n{item[1]}")
        elif item[0] == "file":
            await query.message.reply_document(document=item[2], caption=f"📄 ملف: {btn_name}")

def main():
    TOKEN = os.environ.get('BOT_TOKEN')
    init_db()
    keep_alive()
    app_tg = Application.builder().token(TOKEN).build()
    
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("admin", admin_panel))
    app_tg.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))
    app_tg.add_handler(CallbackQueryHandler(handle_callbacks))
    
    app_tg.run_polling()

if __name__ == '__main__': main()
