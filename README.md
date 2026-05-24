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

После `git clone` ключи подхватываются из `deploy/credentials.bin` автоматически.

**Локально (разработка)** — файл `апи ключи` (см. `апи ключи.example`):

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

## Обновление ключей в репозитории

```bash
python scripts/encode_keys.py
git add deploy/credentials.bin
git commit -m "Update deploy credentials"
git push
```

## Деплой

```bash
git clone https://github.com/Highcoder7/zbot.git
cd zbot
pip install -r requirements.txt
python bot.py
```

Бот использует long polling — нужен процесс 24/7 (VPS, Oracle Cloud Free и т.д.).
