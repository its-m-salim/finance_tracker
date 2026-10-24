from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram import F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import asyncio
import os
import random
from service import *
from connection import*

load_dotenv()

token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="📜 История")],
        [KeyboardButton(text="👤 Профиль")],
    ],
    resize_keyboard=True
)


@dp.message(CommandStart())
async def start_bot(message: Message):
    user = message.from_user
    if not await profile(user.id):
        await message.answer(f"""Привет, {user.full_name}! 👋

💸 Добро пожаловать в «Финансовый трекер»!

Здесь твои финансы под контролем:
📥 записывай доходы;
📤 отслеживай расходы;
💰 следи за балансом;
🎯 планируй цели и отмечай погашение долгов.

Нужна подсказка? Нажми «🆘 Помощь» — расскажу, с чего начать.""", reply_markup=main_keyboard)
        await create_user(user.full_name, user.username, user.id)
    else:
        await message.answer(f"""С возвращением, {user.full_name}! 👋

💰 Продолжаем держать финансы под контролем!
Выбирай действие в меню ниже или введи команду.""", reply_markup=main_keyboard)


@dp.message(Command("help"))
@dp.message(F.text == "🆘 Помощь")
async def command_help(message: Message):
    await message.answer("""💸 ФИНАНСОВЫЙ ТРЕКЕР — ПОМОЩЬ

👤 Профиль
/profile — посмотреть данные профиля и текущий баланс.

💰 Доходы и расходы
/deposit сумма/описание — добавить доход.
/withdraw сумма/описание — добавить расход.

📜 История операций
/history — вся история операций.
/history deposit — только доходы.
/history withdraw — только расходы.
/history last — последняя операция.
/history big — операция с самой большой суммой.

🎯 Цели и долги
/add_goal сумма/описание — создать финансовую цель.
/add_credit сумма/описание — добавить долг.
/goals — показать цели и долги.
/goals goal — показать только цели.
/goals credit — показать только долги.

📈 Прогресс
/pay_goal ID/сумма — отметить пополнение цели.
/pay_credit ID/сумма — отметить погашение долга.

ℹ️ Важно
• Сумма должна быть положительным целым числом.
• Разделяй аргументы символом /.
• Для целей и долгов сначала создай запись, затем используй её ID из списка.

Примеры:
`/deposit 500/Зарплата`
`/withdraw 120/Обед`
`/add_goal 5000/Новый ноутбук`
`/add_credit 2000/Долг другу`""")


@dp.message(Command("profile"))
@dp.message(F.text == "👤 Профиль")
async def command_profile(message: Message):
    user = await profile(message.from_user.id)
    await message.answer(f"""
👤 ТВОЙ ПРОФИЛЬ

🪪 Имя: {user["full_name"]}
🔹 Username: @{user["username"] or "не указан"}
💰 Текущий баланс: {user["balance"]}

Держи финансы под контролем — каждая операция помогает видеть общую картину!
""")


@dp.message(Command("withdraw"))
async def command_withdraw(message: Message, command: CommandObject):
    usr = message.from_user
    if not command.args:
        await message.answer("""Чтобы записать расход, укажи сумму и описание.
Пример: /withdraw 10/Купил молоко

💡 Описание поможет вспомнить, на что ушли деньги.""")
        return
    tran = command.args.split("/")
    if len(tran) < 2:
        await message.answer("""Не хватает данных: нужны и сумма, и описание.
Пример: /withdraw 10/Купил молоко""")
        return
    if len(tran) > 2:
        await message.answer("""Слишком много аргументов. Формат команды: сумма/описание.
Пример: /withdraw 10/Купил молоко""")
        return
    error = check_amount(tran[0])
    if error:
        await message.answer(error)
        return
    amount = int(tran[0])
    caption = tran[1].strip()
    if not caption:
        await message.answer("""Название не может быть пустым. 📝
Добавь короткое и понятное описание.""")
        return
    user = await profile(message.from_user.id)
    if user["balance"] < amount:
        await message.answer("""Недостаточно средств на балансе для этого расхода. 💳
Проверь баланс и попробуй указать меньшую сумму.""")
        return
    else:
        if await make_transactions(caption, usr.id, amount, "withdraw"):
            await message.answer("""✅ Расход записан!

📉 Баланс обновлён. Все детали доступны в разделе «📜 История».""")
        else:
            await message.answer("""Не получилось сохранить расход. ⚠️
Попробуй ещё раз чуть позже.""")


@dp.message(Command("deposit"))
async def command_deposit(message: Message, command: CommandObject):
    usr = message.from_user
    if not command.args:
        await message.answer("""Чтобы записать доход, укажи сумму и описание.
Пример: /deposit 10/Продал молоко

💡 Укажи источник дохода, чтобы история была понятнее.""")
        return
    tran = command.args.split("/")
    if len(tran) < 2:
        await message.answer("""Не хватает данных: нужны и сумма, и описание.
Пример: /deposit 10/Продал молоко""")
        return
    if len(tran) > 2:
        await message.answer("""Слишком много аргументов. Формат команды: сумма/описание.
Пример: /deposit 10/Продал молоко""")
        return
    error = check_amount(tran[0])
    if error:
        await message.answer(error)
        return
    amount = int(tran[0])
    caption = tran[1].strip()
    if not caption:
        await message.answer("""Название не может быть пустым. 📝
Добавь короткое и понятное описание.""")
        return
    user = await profile(message.from_user.id) 
    if await make_transactions(caption, usr.id, amount, "deposit"):
        await message.answer("""✅ Доход записан!

📈 Баланс обновлён — отличный шаг к финансовому порядку!""")
    else:
        await message.answer("""Не получилось сохранить доход. ⚠️
Попробуй ещё раз чуть позже.""")


# @dp.message(F.text == "📋 Мои задачи")
@dp.message(Command("history"))
@dp.message(F.text == "📜 История")
async def command_history(message: Message, command: CommandObject | None = None):
    user = message.from_user
    text = ""
    args = command.args if command else None
    if not args:
        transictions = await get_transictions(message.from_user.id)
    else:
        data = args.split("/")
        if len(data) > 1:
            await message.answer("""Не удалось распознать команду. 🤔
Открой /help и проверь формат примера.""")
            return
        elif data[0].lower() == "last":
            transictions = await get_last_tr(user.id)
            text += "🕘 Твоя последняя операция\n\n"
        elif data[0].lower() == "big":
            transictions = await get_biggest_tr(user.id)
            text += "🏆 Самая крупная операция\n\n"
        elif data[0].lower() in ("withdraw", "deposit"):
            transictions = await get_tr_type(user.id, data[0].lower() )
            text += "➖ Расходы\n" if data[0].lower() == "withdraw" else "➕ Доходы\n"
        else:
            await message.answer("""Не удалось распознать команду. 🤔
Открой /help и проверь формат примера.""")
            return
    if not transictions:
        await message.answer("""📭 История пока пуста.

Добавь первую операцию с помощью /deposit или /withdraw — и здесь появятся её детали.""")
        return
    for tr in transictions:
        tr_type = "Расход" if tr["type"] == "withdraw" else "Доход"
        text += f"""

🧾 Операция №{tr['id']}
📝 Описание: {tr['caption']}
📌 Тип: {tr_type}
💰 Сумма: {tr['amount']}
🕒 Дата: {tr['created_at']}"""
    await message.answer(text)


@dp.message(Command("goals"))
async def command_goals(message: Message, command: CommandObject):
    user = message.from_user
    if not command.args:
        goals = await get_goals(user.id, "credit", "goal")
        text = """🎯 ТВОИ ЦЕЛИ И ДОЛГИ\n\nСледи за прогрессом и двигайся к своим планам шаг за шагом.\n"""
        empty = """Пока здесь пусто. 🌱

Создай финансовую цель через /add_goal или добавь долг через /add_credit."""
    elif command.args.lower() in ("goal", "credit"):
        goal_type = command.args.lower()
        goals = await get_goals(user.id, goal_type, goal_type)
        text = """🎯 ТВОИ ФИНАНСОВЫЕ ЦЕЛИ\n\nКаждый шаг приближает тебя к результату!\n""" if goal_type == "goal" else """💳 ТВОИ ДОЛГИ\n\nОтслеживай погашение и держи всё под контролем.\n"""
        empty = """У тебя пока нет финансовых целей. 🎯

Добавь первую командой /add_goal сумма/описание.""" if goal_type == "goal" else """Долгов пока нет — отличное начало! ✨

Если нужно отслеживать долг, добавь его через /add_credit сумма/описание."""
    else:
        await message.answer("""Не удалось распознать команду. 🤔
Открой /help и проверь формат примера.""")
        return
    if not goals:
        await message.answer(empty)
        return
    for tr in goals:
        item_type = "Финансовая цель" if tr["type"] == "goal" else "Долг"
        progress_label = "Накоплено" if tr["type"] == "goal" else "Погашено"
        status_text = "Завершено" if tr["status"] else "В процессе"
        text += f"""

🆔 Запись №{tr['id']} · {item_type}
📝 Название: {tr['caption']}
💰 Сумма: {tr['amount']}
📊 {progress_label}: {tr['current_amount']}
📍 Статус: {status_text}
🗓 Создано: {tr['created_at']}"""
    await message.answer(text)



@dp.message(Command("add_goal"))
async def add_task(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Укажи сумму и название финансовой цели.
Пример: /add_goal 5000/Новый ноутбук""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает данных: укажи сумму и название цели.
Пример: /add_goal 5000/Новый ноутбук""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Формат команды: сумма/название цели.
Пример: /add_goal 5000/Новый ноутбук""")
        return
    error = check_amount(data[0])
    if error:
        await message.answer(error)
        return
    amount = int(data[0])
    caption = data[1].strip()
    if not caption:
        await message.answer("""Название не может быть пустым. 📝
Добавь короткое и понятное описание.""")
        return
    if await create_goal_credit(caption, amount, message.from_user.id, "goal"):
        await message.answer("""✅ Запись создана!

Теперь её можно найти в списке /goals и отслеживать прогресс.""")
    else:
        await message.answer("""Не удалось создать запись. ⚠️
Проверь сумму и описание, затем попробуй ещё раз.""")


@dp.message(Command("add_credit"))
async def add_task(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Для команды нужны сумма, тип записи и описание.
Пример: /add_credit 2000/Долг другу""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает данных: укажи сумму и описание долга.
Пример: /add_credit 2000/Долг другу""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Формат команды: сумма/описание.
Пример: /add_credit 2000/Долг другу""")
        return
    error = check_amount(data[0])
    if error:
        await message.answer(error)
        return
    amount = int(data[0])
    caption = data[1].strip()
    if not caption:
        await message.answer("""Название не может быть пустым. 📝
Добавь короткое и понятное описание.""")
        return
    if await create_goal_credit(caption, amount, message.from_user.id, "credit"):
        await message.answer("""✅ Запись создана!

Теперь её можно найти в списке /goals и отслеживать прогресс.""")
    else:
        await message.answer("""Не удалось создать запись. ⚠️
Проверь сумму и описание, затем попробуй ещё раз.""")




@dp.message(Command("pay_goal"))
async def pay(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Укажи ID цели и сумму, которую хочешь добавить к прогрессу.
Пример: /pay_goal 1/100""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает данных: нужны ID цели и сумма.
Пример: /pay_goal 1/100""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Формат команды: ID/сумма.
Пример: /pay_goal 1/100""")
        return
    error = check_amount(data[1])
    if error:
        await message.answer(error)
        return
    amount = int(data[1])
    active = await get_status(message.from_user.id, data[0])
    if not active["is_active"]:
        await message.answer("Эта запись уже завершена. 🏆")
        return
    if active["amount"] < active["current_amount"] + amount:
        await message.answer("""Эта сумма превышает остаток до цели. 💡
Укажи сумму не больше оставшейся части.""")
        return
    
    if await pay_goal_credit(amount , data[0], message.from_user.id, "goal"):
        await message.answer("""✅ Запись создана!

Теперь её можно найти в списке /goals и отслеживать прогресс.""")
        if await get_status(message.from_user.id, data[0]):
            await message.answer("🏆 Поздравляю! Цель достигнута!")
    else:
        await message.answer("""Не удалось создать запись. ⚠️
Проверь сумму и описание, затем попробуй ещё раз.""")



@dp.message(Command("pay_credit"))
async def repayments(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Укажи ID долга и сумму погашения.
Пример: /pay_credit 1/100""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает данных: нужны ID долга и сумма погашения.
Пример: /pay_credit 1/100""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Формат команды: ID/сумма.
Пример: /pay_credit 1/100""")
        return
    error = check_amount(data[1])
    if error:
        await message.answer(error)
        return
    amount = int(data[1])
    active = await get_status(message.from_user.id, data[0])
    if not active["is_active"]:
        await message.answer("Эта запись уже завершена. 🏆")
        return
    if active["amount"] < active["current_amount"] + amount:
        await message.answer("""Эта сумма превышает оставшуюся часть долга. 💡
Укажи сумму не больше остатка.""")
        return
    user = await profile(message.from_user.id)
    
    if user["balance"] < amount:
        await message.answer("""Недостаточно средств на балансе для этого расхода. 💳
Проверь баланс и попробуй указать меньшую сумму.""")
        return
    if await pay_goal_credit(amount , data[0], message.from_user.id, "credit"):
        await message.answer("""✅ Запись создана!

Теперь её можно найти в списке /goals и отслеживать прогресс.""")
    else:
        await message.answer("""Не удалось создать запись. ⚠️
Проверь сумму и описание, затем попробуй ещё раз.""")





async def main():
    print("Bot started")
    await create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())