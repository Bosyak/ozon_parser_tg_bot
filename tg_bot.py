import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.fsm.context import FSMContext
import clickhouse_connect
import logging
import os

from config import CLICKHOUSE_CONFIG, API_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _select_to_clickhouse_sync(search_stuff: str):
    """
    СИНХРОННАЯ функция: выполняется в thread pool через asyncio.to_thread,
    чтобы не блокировать event loop aiogram.
    Возвращает кортеж (event_time, title, price, currency, rating, url) или None.
    """
    if not search_stuff:
        return None
    client = None
    try:
        connect_kwargs = {
            'host': CLICKHOUSE_CONFIG['host'],
            'port': CLICKHOUSE_CONFIG['port'],
            'database': CLICKHOUSE_CONFIG['database'],
        }
        if CLICKHOUSE_CONFIG.get('username'):
            connect_kwargs['username'] = CLICKHOUSE_CONFIG['username']
        if CLICKHOUSE_CONFIG.get('password'):
            connect_kwargs['password'] = CLICKHOUSE_CONFIG['password']

        client = clickhouse_connect.get_client(**connect_kwargs)
        logger.info(f"CH OK: {CLICKHOUSE_CONFIG['host']}:{CLICKHOUSE_CONFIG['port']}/{CLICKHOUSE_CONFIG['database']}")
        search_stuff = search_stuff.lower()
        print(search_stuff)
        select_query = f"""
            SELECT event_time, title, card_price, offers_price, offers_priceCurrency, rating, product_url
            FROM {CLICKHOUSE_CONFIG['table']}
            WHERE lowerUTF8(title) LIKE '%{search_stuff}%'
            AND rating > 4
            ORDER BY offers_price
            LIMIT 1
        """
        print(select_query)
        result = client.query(select_query)
        rows = result.result_rows or []
        if not rows:
            return None

        event_time, title, card_price, price, offers_priceCurrency, rating, product_url = rows[0]
        return event_time, title, card_price, price, offers_priceCurrency, rating, product_url

    except Exception as e:
        logger.exception(f"ClickHouse error: {e}")
        return None
    finally:
        if client:
            try:
                client.close()
            except Exception:
                pass

async def select_to_clickhouse(search_stuff: str):
    """
    АСИНХРОННАЯ обёртка: выносит блокирующую работу в отдельный поток.
    """
    return await asyncio.to_thread(_select_to_clickhouse_sync, search_stuff)

# --- aiogram ---

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/help")], [KeyboardButton(text="Добавить товар к поиску")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=keyboard)

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.answer("Отправь мне название товара, и я найду его в базе.\nИли напиши \"Добавить товар к поиску\" и следующим сообщением добавь товар для парсинга")

class AddItem(StatesGroup):
    waiting_for_item = State()

# 1) Триггер на добавление товара к поиску
@dp.message(F.text == "Добавить товар к поиску")
async def add_item_start(message: Message, state: FSMContext):
    await state.set_state(AddItem.waiting_for_item)
    await message.answer("Отправь название товара одной строкой.")

# 2) Принимаем следующее сообщение в состоянии и пишем в файл
@dp.message(AddItem.waiting_for_item, F.text)
async def add_item_save(message: Message, state: FSMContext):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'список для поиска.txt')
    mes = message.text.strip().replace(' ', '+')   
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(mes + '\n')

    await state.clear()
    await message.answer("Товар записан.")

# 3) Универсальный обработчик поиска (когда мы НЕ в состоянии AddItem)
@dp.message(F.text)
async def universal_search(message: Message):
    query = message.text.strip()
    result = await select_to_clickhouse(query)
    if not result:
        await message.answer("Такого товара нет!")
        return
    event_time, title, card_price, price, offers_priceCurrency, rating, product_url = result
    await message.answer("Вот твой товар:")
    await message.answer(title)
    await message.answer(f"Стоимость по карте озон: {card_price} {offers_priceCurrency}")
    await message.answer(f"Стоимость: {price} {offers_priceCurrency}")
    await message.answer(f"Его рейтинг: {rating}")
    await message.answer(f"Время просмотра: {event_time}")
    await message.answer(f"Ссылка на товар:\n{product_url}")

@dp.message()
async def ignore_non_text(message: Message):
    await message.answer("Отправь, пожалуйста, текстовое сообщение.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
