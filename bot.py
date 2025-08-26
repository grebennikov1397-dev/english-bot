import os
import asyncio
from threading import Thread
from random import shuffle
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Please set environment variable BOT_TOKEN")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# глобально сохраним event loop PTB
ptb_loop = None

# ==== контент ====
lessons = {
    1: {"word": "apple", "translate": "яблоко", "example": "I eat an apple every day."},
    2: {"word": "book", "translate": "книга", "example": "This book is very interesting."},
    3: {"word": "dog", "translate": "собака", "example": "The dog is barking."},
}

# ==== handlers ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот.\nКоманды: /lesson /quiz /archive /help")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/lesson — урок дня\n/quiz — викторина\n/archive — архив")

async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = lessons[1]
    await update.message.reply_text(
        f"Слово: {data['word']} → {data['translate']}\nПример: {data['example']}"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = lessons[1]
    options = ["яблоко", "книга", "собака", "машина"]
    shuffle(options)
    buttons = [[InlineKeyboardButton(opt, callback_data=f"quiz:{opt}")] for opt in options]
    await update.message.reply_text(
        f"Как переводится слово: {data['word']}?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choice = q.data.split(":", 1)[1]
    correct = lessons[1]["translate"]
    await q.edit_message_text("✅ Верно!" if choice == correct else f"❌ Правильный ответ: {correct}")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "\n".join([f"{i}. {d['word']} — {d['translate']}" for i, d in lessons.items()])
    await update.message.reply_text("📚 Архив:\n" + text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ты написал: {update.message.text}")

# регистрируем
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("lesson", lesson))
application.add_handler(CommandHandler("quiz", quiz))
application.add_handler(CallbackQueryHandler(quiz_answer, pattern=r"^quiz:"))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ==== запускаем PTB в фоне и сохраняем его loop ====
def _ptb_worker():
    global ptb_loop
    async def _run():
        global ptb_loop
        ptb_loop = asyncio.get_event_loop()
        await application.initialize()
        await application.start()
        await asyncio.Event().wait()
    asyncio.run(_run())

Thread(target=_ptb_worker, daemon=True).start()

# ==== Flask webhook ====
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    from telegram import Update
    update = Update.de_json(request.get_json(force=True), application.bot)
    if ptb_loop:
        asyncio.run_coroutine_threadsafe(
            application.process_update(update), ptb_loop
        )
    return "ok", 200

@app.get("/")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
