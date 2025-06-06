import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from httpx import AsyncClient
from aiogram.utils.keyboard import ReplyKeyboardBuilder


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = Bot(token="ваш токен")
dp = Dispatcher()


# Класс для хранения состояния генерации сценария
class ScenarioState:
    def __init__(self):
        self.theme = None
        self.level = None
        self.length = None
        self.style = None
        self.additional_info = None


# Хранилище состояний пользователей
user_states = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):

    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="🆕 Новый сценарий"),
        types.KeyboardButton(text="⚡ Быстрый сценарий")
    )
    builder.row(types.KeyboardButton(text="ℹ️ Помощь"))

    await message.answer(
        "🎲 *Добро пожаловать в генератор сценариев для D&D!*\n\n"
        "Я помогу вам создать увлекательные приключения для вашей кампании.\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text in ["🆕 Новый сценарий", "⚡ Быстрый сценарий", "ℹ️ Помощь"])
async def handle_main_buttons(message: types.Message):
    if message.text == "🆕 Новый сценарий":
        await cmd_new_scenario(message)
    elif message.text == "⚡ Быстрый сценарий":
        await cmd_quick_scenario(message)
    elif message.text == "ℹ️ Помощь":
        await cmd_help(message)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📖 *Помощь по использованию бота*\n\n"
        "*/new_scenario* - пошаговое создание сценария с настройкой параметров\n"
        "*/quick_scenario* - быстрая генерация сценария с минимальными настройками\n\n"
        "Бот использует GPT4Free для генерации контента, поэтому ответы могут занимать некоторое время."
    )
    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("new_scenario"))
async def cmd_new_scenario(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = ScenarioState()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Фэнтези"), types.KeyboardButton(text="Стимпанк")],
            [types.KeyboardButton(text="Киберпанк"), types.KeyboardButton(text="Хоррор")],
            [types.KeyboardButton(text="Другое")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "🎭 *Выберите тему сценария:*\n\n"
        "1. Фэнтези - классические приключения в мире магии и мечей\n"
        "2. Стимпанк - технологии и магия пара\n"
        "3. Киберпанк - высокие технологии и низкая жизнь\n"
        "4. Хоррор - мрачные и пугающие приключения\n"
        "5. Другое - укажите свою тему",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработка выбора темы
@dp.message(lambda message: message.text in ["Фэнтези", "Стимпанк", "Киберпанк", "Хоррор", "Другое"])
async def process_theme(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return await message.answer("Пожалуйста, начните с команды /new_scenario")

    if message.text == "Другое":
        await message.answer("📝 Введите свою тему сценария:")
        return

    user_states[user_id].theme = message.text

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Новичок (1-3 уровень)")],
            [types.KeyboardButton(text="Опытный (4-10 уровень)")],
            [types.KeyboardButton(text="Ветеран (11-16 уровень)")],
            [types.KeyboardButton(text="Легенда (17-20 уровень)")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "⚔️ *Выберите уровень сложности для персонажей:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработка пользовательской темы
@dp.message(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].theme is None)
async def process_custom_theme(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id].theme = message.text

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Новичок (1-3 уровень)")],
            [types.KeyboardButton(text="Опытный (4-10 уровень)")],
            [types.KeyboardButton(text="Ветеран (11-16 уровень)")],
            [types.KeyboardButton(text="Легенда (17-20 уровень)")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "⚔️ *Выберите уровень сложности для персонажей:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработка выбора уровня сложности
@dp.message(lambda message: message.text in [
    "Новичок (1-3 уровень)",
    "Опытный (4-10 уровень)",
    "Ветеран (11-16 уровень)",
    "Легенда (17-20 уровень)"
])
async def process_level(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states or user_states[user_id].theme is None:
        return await message.answer("Пожалуйста, начните с команды /new_scenario")

    user_states[user_id].level = message.text

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Короткий (1 сессия)")],
            [types.KeyboardButton(text="Средний (2-3 сессии)")],
            [types.KeyboardButton(text="Длинный (4+ сессий)")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "⏳ *Выберите длину сценария:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработка выбора длины сценария
@dp.message(lambda message: message.text in ["Короткий (1 сессия)", "Средний (2-3 сессии)", "Длинный (4+ сессий)"])
async def process_length(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states or user_states[user_id].level is None:
        return await message.answer("Пожалуйста, начните с команды /new_scenario")

    user_states[user_id].length = message.text

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Боевой")],
            [types.KeyboardButton(text="Ролевой")],
            [types.KeyboardButton(text="Исследовательский")],
            [types.KeyboardButton(text="Смешанный")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "🎭 *Выберите стиль игры:*\n\n"
        "1. Боевой - акцент на сражениях и тактике\n"
        "2. Ролевой - акцент на взаимодействии и отыгрыше\n"
        "3. Исследовательский - акцент на изучении мира\n"
        "4. Смешанный - баланс всех элементов",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработка выбора стиля игры
@dp.message(lambda message: message.text in ["Боевой", "Ролевой", "Исследовательский", "Смешанный"])
async def process_style(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states or user_states[user_id].length is None:
        return await message.answer("Пожалуйста, начните с команды /new_scenario")

    user_states[user_id].style = message.text

    await message.answer(
        "💡 *Есть ли дополнительные пожелания или детали для сценария?*\n\n"
        "Например: конкретные локации, NPC, сюжетные повороты или что-то еще. "
        "Если нет, просто напишите 'нет'.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )


# Обработка дополнительной информации
@dp.message(
    lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].style is not None and
                    user_states[message.from_user.id].additional_info is None)
async def process_additional_info(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]

    if message.text.lower() != "нет":
        state.additional_info = message.text

    # промпт для GPT
    prompt = (
        f"Создай детализированный сценарий для Dungeons & Dragons со следующими параметрами:\n"
        f"- Тема: {state.theme}\n"
        f"- Уровень сложности: {state.level}\n"
        f"- Длина: {state.length}\n"
        f"- Стиль игры: {state.style}\n"
    )

    if state.additional_info:
        prompt += f"- Дополнительные пожелания: {state.additional_info}\n"

    prompt += (
        "\nСценарий должен включать:\n"
        "1. Краткое описание сюжета (1-2 абзаца)\n"
        "2. Основные локации с описанием\n"
        "3. Ключевых NPC с характеристиками\n"
        "4. Возможные сюжетные повороты\n"
        "5. Рекомендуемые столкновения/сражения\n"
        "6. Награды для персонажей\n"
        "\nОформи ответ в виде красивого Markdown-документа."
    )

    await message.answer("🪄 *Начинаю генерацию сценария...* Это может занять некоторое время.", parse_mode="Markdown")

    try:
        response = await gpt_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        scenario_text = response.choices[0].message.content

        if len(scenario_text) > 4000:
            parts = [scenario_text[i:i + 4000] for i in range(0, len(scenario_text), 4000)]
            for part in parts:
                await message.answer(part, parse_mode="Markdown")
        else:
            await message.answer(scenario_text, parse_mode="Markdown")

        await message.answer("✨ *Сценарий готов!* Хорошей игры!", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при генерации сценария: {e}")
        await message.answer("⚠️ Произошла ошибка при генерации сценария. Пожалуйста, попробуйте позже.")

    del user_states[user_id]


@dp.message(Command("quick_scenario"))
async def cmd_quick_scenario(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Фэнтези"), types.KeyboardButton(text="Стимпанк")],
            [types.KeyboardButton(text="Киберпанк"), types.KeyboardButton(text="Хоррор")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "🎲 *Быстрая генерация сценария D&D*\n\n"
        "Выберите тему для сценария:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработка быстрой генерации
@dp.message(
    lambda message: message.text in ["Фэнтези", "Стимпанк", "Киберпанк", "Хоррор"] and not message.text.startswith('/'))
async def process_quick_scenario(message: types.Message):
    theme = message.text

    await message.answer(
        f"🪄 *Начинаю генерацию {theme.lower()} сценария...* Это может занять некоторое время.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

    try:
        response = await gpt_client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": (
                    f"Создай краткий, но детализированный сценарий для Dungeons & Dragons 5e в {theme.lower()} сеттинге. "
                    "Сценарий должен включать:\n"
                    "1. Краткое описание сюжета (1 абзац)\n"
                    "2. 2-3 ключевые локации\n"
                    "3. 2-3 важных NPC\n"
                    "4. 1-2 возможных сражения\n"
                    "5. Награды для персонажей\n"
                    "\nОформи ответ в виде Markdown."
                )
            }],
            temperature=0.7,
            max_tokens=1500
        )

        scenario_text = response.choices[0].message.content
        await message.answer(scenario_text, parse_mode="Markdown")
        await message.answer("✨ *Сценарий готов!* Хорошей игры!", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при быстрой генерации сценария: {e}")
        await message.answer("⚠️ Произошла ошибка при генерации сценария. Пожалуйста, попробуйте позже.")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())