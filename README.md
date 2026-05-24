# Zinotti Telegram Bot (zbot)

Telegram-бот для Zinotti: генерация казахских транскриптов по фото мебели и кратких сценариев Reels.

## Возможности

- **Транскрипт** — черновик по фото → уточнение размеров и материалов → финальный текст на казахском
- **Контент-сценарий** — 2 варианта (развлекательный + лайфхак): описание, транскрипт, смысл, цель видео

## Установка

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Настройка ключей

**Вариант A** — файл `апи ключи` (см. `апи ключи.example`):

```
tg api key = YOUR_BOT_TOKEN
open ai api key = YOUR_OPENAI_KEY
open ai content model = "gpt-5.5"
```

**Вариант B** — `.env` (скопируйте `.env.example`):

```bash
cp .env.example .env
```

## Запуск

```bash
python bot.py
```

## Модели

- Сценарии и транскрипты: `OPENAI_CONTENT_MODEL` (по умолчанию `gpt-5.5`)
- Fallback: Claude (если OpenAI недоступен)

## Деплой

Бот использует long polling — нужен процесс, работающий 24/7 (VPS, Oracle Cloud Free, Fly.io и т.д.). Секреты храните только в переменных окружения на сервере, не в Git.
