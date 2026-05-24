import asyncio
import logging
import io
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

import config
import prompts
import ai_service

# --- Setup Logger ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ZinottiBot.Bot")

# --- Initialize Bot and Dispatcher ---
if not config.TG_BOT_TOKEN:
    logger.error("TG_BOT_TOKEN is not defined! Please check the 'апи ключи' file.")
    raise ValueError("TG_BOT_TOKEN is missing! Bot cannot start.")

bot = Bot(token=config.TG_BOT_TOKEN)
dp = Dispatcher()

# --- FSM States ---
class TranscriptStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_details = State()  # Sizes & Materials

class ScenarioStates(StatesGroup):
    waiting_for_product = State()   # Photo or name of furniture
    waiting_for_vibe = State()      # Selection of aesthetic vibe or custom text
    waiting_for_features = State()  # Features or skip button

# --- Keyboards ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать транскрипт (По фото)")],
            [KeyboardButton(text="🎬 Контент-сценарий (Reels/TikTok)")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите нужное действие..."
    )

def get_cancel_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_vibe_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 Quiet Luxury (Тихая роскошь)")],
            [KeyboardButton(text="☁️ Скандинавский дзен"), KeyboardButton(text="☕ Cozy Core (Уютный вечер)")],
            [KeyboardButton(text="📐 Tactical Minimalism"), KeyboardButton(text="🍂 Дождливое утро в Милане")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите вайб или напишите свой..."
    )

def get_skip_features_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Сгенерировать сценарий")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_retry_inline_keyboard(action_type):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сгенерировать заново", callback_data=f"retry_{action_type}")]
        ]
    )


# --- General Handlers ---

@dp.message(Command("start", "menu"))
async def cmd_start_menu(message: types.Message, state: FSMContext):
    await state.set_state(None)  # Reset state but keep potential data
    welcome_text = (
        "🛋️ **Добро пожаловать в Zinotti Content Bot!**\n\n"
        "Я помогу вам создавать первоклассный контент для мебельного магазина **Zinotti**.\n\n"
        "Вы можете:\n"
        "1. **Написать транскрипт по фото** — отправьте мне фото мебели, я составлю черновик на казахском языке в фирменном стиле, "
        "запрошу размеры/материалы и подготовлю идеальный финальный текст для видео/аудио.\n"
        "2. **Создать контент-сценарий** — отправьте фото мебели или опишите идею/товар словами. Я составлю 2 мощных Reels/TikTok сценария: "
        "развлекательный (с психологическими триггерами) и экспертный (полезные лайфхаки).\n\n"
        "Выберите действие в меню ниже 👇"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.message(F.text == "❌ Отмена")
@dp.message(Command("cancel"))
async def action_cancel(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("Действие отменено. Возврат в главное меню.", reply_markup=get_main_menu())

# ==========================================
# FLOW 1: Transcript Generator (Photo + Details)
# ==========================================

@dp.message(F.text == "✍️ Написать транскрипт (По фото)")
async def transcript_start(message: types.Message, state: FSMContext):
    await state.set_state(TranscriptStates.waiting_for_photo)
    await message.answer(
        "📸 **Отправьте мне фотографию мебели** (дивана, кровати, кресла и т.д.), "
        "для которой нужно составить транскрипт:",
        reply_markup=get_cancel_menu(),
        parse_mode="Markdown"
    )

@dp.message(TranscriptStates.waiting_for_photo, F.photo)
async def transcript_handle_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    msg_wait = await message.answer("Анализирую фото и создаю черновик транскрипта... ⏳")
    
    try:
        # Download photo to bytes
        file_buffer = io.BytesIO()
        await bot.download(photo, destination=file_buffer)
        image_bytes = file_buffer.getvalue()
        
        # Save photo bytes in context for potentially retrying draft
        await state.update_data(photo_bytes=image_bytes)
        
        # Generate initial draft transcript using AI Service
        draft = await ai_service.generate_draft_transcript_from_photo(image_bytes)
        await state.update_data(draft_transcript=draft)
        
        await msg_wait.delete()
        
        # Send draft to user
        draft_msg = (
            "📝 **Черновик транскрипта (по фото):**\n\n"
            f"`{draft}`\n\n"
            "💬 Теперь напишите **размеры и материалы** этой мебели через запятую "
            "(например: *90x200, букле* или *300x180, велюр*), чтобы я встроил их в финальный транскрипт:"
        )
        await state.set_state(TranscriptStates.waiting_for_details)
        await message.answer(draft_msg, reply_markup=get_cancel_menu(), parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in transcript_handle_photo: {e}")
        await msg_wait.edit_text(
            "❌ Произошла ошибка при анализе фотографии. Пожалуйста, убедитесь в правильности API ключей в файле 'апи ключи' или попробуйте другое фото."
        )

@dp.message(TranscriptStates.waiting_for_photo)
async def transcript_waiting_photo_invalid(message: types.Message):
    await message.answer("Пожалуйста, отправьте именно **фотографию** мебели или нажмите '❌ Отмена'.")

@dp.message(TranscriptStates.waiting_for_details, F.text)
async def transcript_handle_details(message: types.Message, state: FSMContext):
    details_text = message.text
    data = await state.get_data()
    draft = data.get("draft_transcript")
    
    if not draft:
        await message.answer("Произошла ошибка (не найден черновик). Пожалуйста, начните сначала.", reply_markup=get_main_menu())
        await state.set_state(None)
        return
        
    # Split sizes and materials by comma (or use the raw input)
    parts = [p.strip() for p in details_text.split(",", 1)]
    sizes = parts[0]
    materials = parts[1] if len(parts) > 1 else "высококачественные материалы"
    
    # Save parameters for potential retries
    await state.update_data(sizes=sizes, materials=materials)
    
    msg_wait = await message.answer("Дорабатываю транскрипт с учетом размеров и материалов... ⏳")
    
    try:
        final_transcript = await ai_service.refine_transcript_with_details(draft, sizes, materials)
        await state.update_data(final_transcript=final_transcript)
        
        await msg_wait.delete()
        
        result_msg = (
            "✨ **Финальный транскрипт готов!** ✨\n\n"
            f"`{final_transcript}`\n\n"
            "Вы можете скопировать этот текст для озвучки или наложить на видео."
        )
        await message.answer(result_msg, reply_markup=get_main_menu(), parse_mode="Markdown")
        await state.set_state(None) # Reset state but keep data for retry inline callback
        
        # Also offer retry button
        await message.answer("Хотите перегенерировать финальный транскрипт?", reply_markup=get_retry_inline_keyboard("transcript"))
        
    except Exception as e:
        logger.error(f"Error in transcript_handle_details: {e}")
        await msg_wait.edit_text("❌ Произошла ошибка при доработке текста. Пожалуйста, попробуйте позже.")

# ==========================================
SCENARIO_CHUNK_SIZE = 4000


async def send_scenario_messages(target: types.Message, text: str) -> None:
    """Send formatted scenarios to user, splitting if needed."""
    formatted = ai_service.format_scenario_response(text)
    if len(formatted) > SCENARIO_CHUNK_SIZE:
        for i in range(0, len(formatted), SCENARIO_CHUNK_SIZE):
            await target.answer(formatted[i : i + SCENARIO_CHUNK_SIZE], parse_mode="Markdown")
    else:
        await target.answer(formatted, parse_mode="Markdown")


# FLOW 2: Content Scenarios (Entertainment + Lifehacks)
# ==========================================

@dp.message(F.text == "🎬 Контент-сценарий (Reels/TikTok)")
async def scenario_start(message: types.Message, state: FSMContext):
    await state.set_state(ScenarioStates.waiting_for_product)
    await message.answer(
        "🎬 **Генерация сценариев по Золотому Промпту (Шаг 1 из 3)**\n\n"
        "Отправьте мне **фотографию мебели** ИЛИ напишите её **название / тему** "
        "(например: *диван Modena*, *кровать в форме мишки*):",
        reply_markup=get_cancel_menu(),
        parse_mode="Markdown"
    )

@dp.message(ScenarioStates.waiting_for_product, F.photo)
async def scenario_handle_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    
    try:
        file_buffer = io.BytesIO()
        await bot.download(photo, destination=file_buffer)
        image_bytes = file_buffer.getvalue()
        
        await state.update_data(
            scenario_photo_bytes=image_bytes,
            scenario_product="Премиальная мебель (с фотографии)"
        )
        
        await state.set_state(ScenarioStates.waiting_for_vibe)
        await message.answer(
            "📸 Фотография принята!\n\n"
            "✨ **Шаг 2 из 3: Выберите стиль и атмосферу (Vibe Check)**\n"
            "Выберите один из эстетических стилей на клавиатуре ниже или введите свой вариант текста:",
            reply_markup=get_vibe_menu()
        )
    except Exception as e:
        logger.error(f"Error downloading photo in scenario: {e}")
        await message.answer("❌ Ошибка загрузки фото. Пожалуйста, попробуйте еще раз.")

@dp.message(ScenarioStates.waiting_for_product, F.text)
async def scenario_handle_product_text(message: types.Message, state: FSMContext):
    product_name = message.text
    await state.update_data(
        scenario_product=product_name,
        scenario_photo_bytes=None
    )
    
    await state.set_state(ScenarioStates.waiting_for_vibe)
    await message.answer(
        f"🛋️ Мебель/Тема: *{product_name}*\n\n"
        "✨ **Шаг 2 из 3: Выберите стиль и атмосферу (Vibe Check)**\n"
        "Выберите один из эстетических стилей на клавиатуре ниже или введите свой вариант текста:",
        reply_markup=get_vibe_menu(),
        parse_mode="Markdown"
    )

@dp.message(ScenarioStates.waiting_for_vibe, F.text)
async def scenario_handle_vibe(message: types.Message, state: FSMContext):
    selected_vibe = message.text
    await state.update_data(scenario_vibe=selected_vibe)
    
    await state.set_state(ScenarioStates.waiting_for_features)
    await message.answer(
        "🎨 **Шаг 3 из 3: Особенности мебели и детали**\n\n"
        "Напишите ключевые фишки или характеристики мебели через запятую "
        "(например: *букле, песочный цвет, скругленные углы*), "
        "либо нажмите кнопку ниже для мгновенной генерации:",
        reply_markup=get_skip_features_menu(),
        parse_mode="Markdown"
    )

@dp.message(ScenarioStates.waiting_for_features, F.text)
async def scenario_handle_features_and_generate(message: types.Message, state: FSMContext):
    features_input = message.text
    if features_input == "🚀 Сгенерировать сценарий":
        features_input = "Классический премиальный дизайн Zinotti"
        
    await state.update_data(scenario_features=features_input)
    data = await state.get_data()
    
    product = data.get("scenario_product")
    vibe = data.get("scenario_vibe")
    features = data.get("scenario_features")
    image_bytes = data.get("scenario_photo_bytes")
    
    structured_input_summary = (
        "📥 **Запрос принят**\n"
        f"🛋️ {product}\n"
        f"✨ {vibe}\n"
        f"🎨 {features}\n\n"
        "Генерирую краткие сценарии... ⏳"
    )
    await message.answer(structured_input_summary, parse_mode="Markdown", reply_markup=get_main_menu())
    
    msg_wait = await message.answer("Создаю 2 сценария (описание, транскрипт, смысл, цель)... ⏳")
    
    try:
        scenarios = await ai_service.generate_content_scenarios(
            product=product,
            vibe=vibe,
            features=features,
            image_bytes=image_bytes
        )
        await state.update_data(last_scenario=scenarios)
        
        await msg_wait.delete()
        
        await message.answer("🌟 **Сценарии готовы**", parse_mode="Markdown")
        await send_scenario_messages(message, scenarios)
            
        await state.set_state(None) # Reset state but keep context for retry
        await message.answer("Хотите перегенерировать сценарии по этой теме?", reply_markup=get_retry_inline_keyboard("scenario"))
        
    except Exception as e:
        logger.error(f"Error generating scenarios: {e}")
        await msg_wait.edit_text("❌ Произошла ошибка при генерации сценариев. Пожалуйста, попробуйте позже.")


# ==========================================
# FLOW 3: Retry Callbacks (Inline buttons)
# ==========================================

@dp.callback_query(F.data.startswith("retry_"))
async def callback_retry(callback: types.CallbackQuery, state: FSMContext):
    action_type = callback.data.split("_")[1]
    data = await state.get_data()
    
    # Remove inline button from previous message
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
        
    if action_type == "transcript":
        draft = data.get("draft_transcript")
        sizes = data.get("sizes")
        materials = data.get("materials")
        
        if draft and sizes and materials:
            await callback.message.answer("Перегенерирую финальный транскрипт... ⏳")
            try:
                final_transcript = await ai_service.refine_transcript_with_details(draft, sizes, materials)
                await state.update_data(final_transcript=final_transcript)
                
                result_msg = (
                    "✨ **Обновленный финальный транскрипт:** ✨\n\n"
                    f"`{final_transcript}`"
                )
                await callback.message.answer(result_msg, parse_mode="Markdown")
                await callback.message.answer("Хотите перегенерировать еще раз?", reply_markup=get_retry_inline_keyboard("transcript"))
            except Exception as e:
                logger.error(f"Retry transcript error: {e}")
                await callback.message.answer("❌ Произошла ошибка при перегенерации.")
        else:
            await callback.message.answer("К сожалению, данные для перегенерации утеряны. Пожалуйста, начните сначала.")
            
    elif action_type == "scenario":
        product = data.get("scenario_product", "Премиальная мебель Zinotti")
        vibe = data.get("scenario_vibe", "Quiet Luxury")
        features = data.get("scenario_features", "Классический премиальный стиль")
        image_bytes = data.get("scenario_photo_bytes")
        
        await callback.message.answer("Перегенерирую сценарии... ⏳")
        try:
            scenarios = await ai_service.generate_content_scenarios(
                product=product,
                vibe=vibe,
                features=features,
                image_bytes=image_bytes
            )
            await state.update_data(last_scenario=scenarios)
            
            await callback.message.answer("🌟 **Обновлённые сценарии**", parse_mode="Markdown")
            await send_scenario_messages(callback.message, scenarios)
                
            await callback.message.answer("Хотите перегенерировать еще раз?", reply_markup=get_retry_inline_keyboard("scenario"))
        except Exception as e:
            logger.error(f"Retry scenario error: {e}")
            await callback.message.answer("❌ Произошла ошибка при перегенерации.")
            
    await callback.answer()

# ==========================================
# Main Polling Starter
# ==========================================

async def main():
    logger.info("Starting Telegram Bot Polling...")
    # Delete webhook to make sure polling doesn't conflict
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
