import os
import asyncio
from threading import Thread
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Please set environment variable BOT_TOKEN")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # пример: https://english-bot-cew9.onrender.com/<ТОКЕН>

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# ====== контент ======
lessons = {
    1: {"word": "apple", "translate": "яблоко", "example": "I eat an apple every day."},
    2: {"word": "book", "translate": "книга", "example": "This book is very interesting."},
    3: {"word": "dog", "translate": "собака", "example": "The dog is barking."},
}

# ====== хэндлеры ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    param = context.args[0] if context.args else None
    text = ("Привет! Я бот «Английский за 5 минут».\n"
            "Команды:\n/lesson — урок дня\n/quiz — викторина\n/archive — архив уроков\n/help — помощь\n")
    if param:
        text += f"\nТы пришёл по диплинку: {param} (бонусы появятся позже)"
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/lesson — урок дня\n/quiz — викторина\n/archive — архив уроков")

async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = (len(context.user_data) % len(lessons)) + 1
    data = lessons[idx]
    text = (f"📘 Урок дня\n\n"
            f"Слово: *{data['word']}*\n"
            f"Перевод: {data['translate']}\n"
            f"Пример: {data['example']}")
    await update.message.reply_text(text, parse_mode="Markdown")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = lessons[1]
    options = ["яблоко", "книга", "собака", "машина"]
    buttons = [[InlineKeyboardButton(opt, callback_data=f"quiz:{opt}")] for opt in options]
    await update.message.reply_text(
        f"Как переводится слово: *{data['word']}*?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choice = q.data.split(":", 1)[1]
    correct = lessons[1]["translate"]
    await q.edit_message_text("✅ Верно!" if choice == correct else f"❌ Неправильно. Правильный ответ: {correct}")

async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📚 Архив уроков:\n"
    for i, data in lessons.items():
        text += f"{i}. {data['word']} — {data['translate']} ({data['example']})\n"
    text += "\n⚡ В будущем часть архива можно сделать премиум."
    await update.message.reply_text(text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ты написал: {update.message.text}")

# регистрация
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("lesson", lesson))
application.add_handler(CommandHandler("quiz", quiz))
application.add_handler(CallbackQueryHandler(quiz_answer, pattern=r"^quiz:"))
application.add_handler(CommandHandler("archive", archive))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ====== СТАРТУЕМ PTB-ДВИЖОК В ФОНЕ ======
def _ptb_worker():
    async def _run():
        # запускаем приложение, НО без polling/webhook-сервера — приём делает Flask
        await application.initialize()
        await application.start()
        # держим цикл живым
        await asyncio.Event().wait()
    asyncio.run(_run())

Thread(target=_ptb_worker, daemon=True).start()

# ====== Flask endpoint для Telegram ======
import asyncio

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    # отправляем задачу прямо в event loop PTB
    asyncio.run_coroutine_threadsafe(
        application.process_update(update),
        application.loop
    )
    return "ok", 200

@app.get("/")
def health():
    return "ok", 200

# локальный запуск
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
