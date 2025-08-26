import os
import asyncio
from threading import Thread
from random import shuffle
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# === Config ===
TOKEN = os.getenv("BOT_TOKEN")  # задайте на Render во вкладке Environment
if not TOKEN:
    raise RuntimeError("Please set environment variable BOT_TOKEN")

# === Flask (для Render health-check) ===
app = Flask(__name__)

@app.get("/")
def health():
    # Render проверяет, что web-сервис слушает порт и отвечает 200
    return "ok", 200

# === Telegram Application ===
application = Application.builder().token(TOKEN).build()

# --- Sample lessons (расширяйте) ---
lessons = {
    1: {"word": "apple", "translate": "яблоко", "example": "I eat an apple every day."},
    2: {"word": "book", "translate": "книга", "example": "This book is very interesting."},
    3: {"word": "dog", "translate": "собака", "example": "The dog is barking."},
}

# --- Handlers ---
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
    data = lessons[1]  # можно выбрать случайный
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
        tex
