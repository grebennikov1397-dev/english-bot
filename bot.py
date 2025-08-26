
import os
import threading
from flask import Flask
from random import shuffle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# === Config ===
TOKEN = os.getenv("BOT_TOKEN")  # Set BOT_TOKEN in environment (BotFather token)
if not TOKEN:
    raise RuntimeError("Please set environment variable BOT_TOKEN")

# === Flask (health check / Render web service target) ===
app = Flask(__name__)

@app.get("/")
def health():
    return "ok", 200

# === Telegram Application ===
application = Application.builder().token(TOKEN).build()

# --- Sample lessons DB (extend as you like) ---
lessons = {
    1: {"word": "apple", "translate": "яблоко", "example": "I eat an apple every day."},
    2: {"word": "book", "translate": "книга", "example": "This book is very interesting."},
    3: {"word": "dog", "translate": "собака", "example": "The dog is barking."},
}

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    param = context.args[0] if context.args else None
    text = (
        "Привет! Я бот «Английский за 5 минут».\n"
        "Команды:\n"
        "/lesson — урок дня\n"
        "/quiz — викторина\n"
        "/archive — архив уроков\n"
        "/help — помощь\n"
    )
    if param:
        text += f"\nТы пришёл по диплинку: {param} (бонусы появятся позже)"
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/lesson — урок дня\n/quiz — викторина\n/archive — архив уроков"
    )

async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # naive rotation per-user
    idx = (len(context.user_data) % len(lessons)) + 1
    data = lessons[idx]
    text = (
        f"📘 Урок дня\n\n"
        f"Слово: *{data['word']}*\n"
        f"Перевод: {data['translate']}\n"
        f"Пример: {data['example']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = lessons[1]  # or choose randomly
    options = ["яблоко", "книга", "собака", "машина"]
    shuffle(options)
    buttons = [[InlineKeyboardButton(opt, callback_data=f"quiz:{opt}")] for opt in options]
    await update.message.reply_text(
        f"Как переводится слово: *{data['word']}*?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":", 1)[1]
    correct = lessons[1]["translate"]
    if choice == correct:
        await query.edit_message_text("✅ Верно!")
    else:
        await query.edit_message_text(f"❌ Неправильно. Правильный ответ: {correct}")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📚 Архив уроков:\n"
    for i, data in lessons.items():
        text += f"{i}. {data['word']} — {data['translate']} ({data['example']})\n"
    text += "\n⚡ В будущем часть архива можно сделать премиум."
    await update.message.reply_text(text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ты написал: {update.message.text}")

# --- Register handlers ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("lesson", lesson))
application.add_handler(CommandHandler("quiz", quiz))
application.add_handler(CallbackQueryHandler(quiz_answer, pattern=r"^quiz:"))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# === Start long polling in a background thread ===
def _run_polling():
    application.run_polling(drop_pending_updates=True)

# Start polling when the module is imported (works with gunicorn/flask)
threading.Thread(target=_run_polling, daemon=True).start()

if __name__ == "__main__":
    # Local run: just run polling in foreground
    application.run_polling(drop_pending_updates=True)
