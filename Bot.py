```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = '8329740555:AAG3zHjsI2pHxF7Z8ecoj0Kr0ISMU2hjqtk'

MENU_BUTTONS = [
    ("رياضيات", "math"),
    ("تنظيم حاسوب 💻", "computer"),
    ("English", "english"),
    ("كيمياء 🧪🔮", "chemistry"),
    ("برمجة نظري 😁🖥", "programming"),
    ("رسم هندسي نظري 👨‍🎨🎨", "engineering"),
    ("فيزياء نظري 👩‍🔬📉", "physics"),
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(text=name, callback_data=code)] for name, code in MENU_BUTTONS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر القسم:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "math":
        await query.edit_message_text(text="محتوى الرياضيات")
    elif data == "computer":
        await query.edit_message_text(text="محتوى تنظيم الحاسوب")
    elif data == "english":
        await query.edit_message_text(text="محتوى English")
    elif data == "chemistry":
await query.edit_message_text(text="محتوى الكيمياء")
    elif data == "programming":
        await query.edit_message_text(text="محتوى البرمجة النظرية")
    elif data == "engineering":
        await query.edit_message_text(text="محتوى الرسم الهندسي النظري")
    elif data == "physics":
        await query.edit_message_text(text="محتوى الفيزياء النظرية")
    else:
        await query.edit_message_text(text="لا يوجد محتوى لهذا القسم.")

if _name_ == '_main_':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
```