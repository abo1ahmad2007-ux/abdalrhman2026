import os
import sqlite3
import datetime
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# 1. نظام الحماية واستمرارية العمل
app = Flask('')
@app.route('/')
def home(): return "سيستم الإدارة الاحترافي يعمل 24/7"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# 2. قاعدة البيانات الشاملة (للأزرار، الطلاب، والإحصائيات)
def init_db():
    conn = sqlite3.connect('pro_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (user_id INTEGER PRIMARY KEY, name TEXT, year TEXT, info TEXT, join_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS content (name TEXT PRIMARY KEY, type TEXT, val TEXT, file_id TEXT, order_index INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

ADMIN_ID = 8560721192 

# --- القائمة الرئيسية (للطالب) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('pro_system.db')
    student = conn.execute("SELECT * FROM students WHERE user_id=?", (user_id,)).fetchone()
    
    # تحديث إحصائيات الدخول (للمستخدمين الجدد)
    if not student:
        today = datetime.date.today().isoformat()
        conn.execute("INSERT OR IGNORE INTO students (user_id, join_date) VALUES (?, ?)", (user_id, today))
        conn.commit()

    btns = conn.execute("SELECT name FROM content ORDER BY order_index ASC").fetchall()
    conn.close()

    keyboard = []
    if not student or not student[1]: # إذا لم يسجل بياناته بعد
        keyboard.append([InlineKeyboardButton("📝 تسجيل بيانات الطالب", callback_data='reg_start')])
    
    # ترتيب الأزرار المضافة
    for i in range(0, len(btns), 2):
        row = [InlineKeyboardButton(btns[i][0], callback_data=f"show_{btns[i][0]}")]
        if i + 1 < len(btns): row.append(InlineKeyboardButton(btns[i+1][0], callback_data=f"show_{btns[i+1][0]}"))
        keyboard.append(row)

    msg = "🎓 **أهلاً بك في المنصة الطلابية**\nيرجى اختيار القسم المطلوب من الأسفل:"
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- لوحة تحكم الأدمن (مطابقة للصورة) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    keyboard = [
        [InlineKeyboardButton("⚙️ تشغيل البوت", callback_data='none'), InlineKeyboardButton("✅", callback_data='none')],
        [InlineKeyboardButton("📊 قسم الإحصائيات", callback_data='adm_stats'), InlineKeyboardButton("📢 قسم الإذاعة", callback_data='adm_broadcast')],
        [InlineKeyboardButton("🔘 تعديل الأزرار", callback_data='adm_btns'), InlineKeyboardButton("🔄 ترتيب الأزرار", callback_data='adm_reorder')],
        [InlineKeyboardButton("👥 قسم المشرفين", callback_data='adm_mods'), InlineKeyboardButton("📥 النسخة الاحتياطية", callback_data='adm_backup')],
        [InlineKeyboardButton("📄 رسالة الترحيب (start)", callback_data='adm_welcome')],
        [InlineKeyboardButton("⭐ الاشتراك المدفوع", callback_data='adm_premium')]
    ]
    await update.message.reply_text("🛠 **لوحة تحكم المدير العام**\nأهلاً بك يا مهندس عبد الرحمن، اختر القسم المراد إدارته:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- معالجة الضغط على الأزرار (Callbacks) ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'adm_stats':
        conn = sqlite3.connect('pro_system.db')
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        reg_count = conn.execute("SELECT COUNT(*) FROM students WHERE name IS NOT NULL").fetchone()[0]
        conn.close()
        await query.message.reply_text(f"📊 **إحصائيات البوت:**\n\n👥 إجمالي المستخدمين: {count}\n✅ الطلاب المسجلين: {reg_count}")

    elif data == 'adm_btns':
        keyboard = [[InlineKeyboardButton("➕ إضافة زر جديد", callback_data='add_btn_flow')],
                    [InlineKeyboardButton("🗑 حذف زر", callback_data='del_btn_flow')],
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_admin')]]
        await query.edit_message_text("🔘 **إدارة الأزرار:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'reg_start':
        context.user_data['reg_state'] = 'name'
        await query.message.reply_text("يرجى إرسال اسمك الثلاثي:")

# --- معالجة الإدخالات النصية ---
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and context.user_data.get('admin_action') == 'broadcasting':
        # نظام الإذاعة
        conn = sqlite3.connect('pro_system.db')
        users = conn.execute("SELECT user_id FROM students").fetchall()
        conn.close()
        for user in users:
            try: await context.bot.send_message(chat_id=user[0], text=update.message.text)
            except: pass
        await update.message.reply_text("✅ تم إرسال الإذاعة للجميع.")
        context.user_data.clear()
        return

    # نظام تسجيل الطالب
    state = context.user_data.get('reg_state')
    if state == 'name':
        context.user_data['temp_name'] = update.message.text
        context.user_data['reg_state'] = 'year'
        await update.message.reply_text("تمام، الحين أرسل سنتك الدراسية (مثلاً: سنة أولى):")
    elif state == 'year':
        name = context.user_data['temp_name']
        year = update.message.text
        conn = sqlite3.connect('pro_system.db')
        conn.execute("UPDATE students SET name=?, year=? WHERE user_id=?", (name, year, update.effective_user.id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ تم تسجيلك بنجاح يا {name}! أرسل /start لرؤية الأقسام.")
        context.user_data.clear()

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
