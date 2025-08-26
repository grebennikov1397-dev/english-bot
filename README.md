
# Telegram Bot: Английский за 5 минут — бесплатная версия

Готовый к деплою бот: бесплатные уроки, викторина, архив. Монетизацию (Stars) можно добавить позже.

## Локальный запуск (простой)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export BOT_TOKEN="ВАШ_ТОКЕН_ОТ_BOTFATHER"
python bot.py  # запустит polling локально (Flask не обязателен)
```

## Локальный запуск (через Flask для проверки web-сервиса)
> Важно: отключаем авто-релоад, чтобы не было двойного импорта.
```bash
export BOT_TOKEN="ВАШ_ТОКЕН_ОТ_BOTFATHER"
flask --app bot --no-reload run --port=8080
```

## Деплой на Render (Web Service)
1. Залейте в GitHub файлы: `bot.py`, `requirements.txt`, `Procfile`, `README.md`.
2. На https://render.com → **New +** → **Web Service** → выберите репозиторий.
3. Настройки:
   - **Environment:** Python
   - **Build Command:**
     ```
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```
     gunicorn bot:app
     ```
   - (у нас в Procfile задано `--workers 1`, так что один воркер гарантирован)
4. Во вкладке **Environment** добавьте переменную:
   ```
   BOT_TOKEN = ваш_токен_от_BotFather
   ```
5. Нажмите **Create Web Service**. Через минуту бот заработает (long polling), а корень `/` будет отвечать `ok`.

### Проверка
В Telegram откройте своего бота и попробуйте команды:
- `/lesson` — урок дня
- `/quiz` — викторина
- `/archive` — архив

## Что дальше
- Расширяйте словарь `lessons` в `bot.py`.
- Когда будете готовы к монетизации — добавим оплату **Telegram Stars** и проверку премиум-доступа (совместим с этим шаблоном).
