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

💰 Добро пожаловать в финансовый трекер!
Здесь ты можешь следить за доходами, расходами и своим балансом.

Нажми «🆘 Помощь», чтобы посмотреть доступные команды.""", reply_markup=main_keyboard)
        await create_user(user.full_name, user.username, user.id)
    else:
        await message.answer(f"""С возвращением, {user.full_name}! 👋

Рад снова тебя видеть.""", reply_markup=main_keyboard)


@dp.message(Command("help"))
@dp.message(F.text == "🆘 Помощь")
async def command_help(message: Message):
    await message.answer("""💰 ПОМОЩЬ ПО ФИНАНСОВОМУ ТРЕКЕРУ

👤 /profile — посмотреть профиль и баланс
➕ /deposit сумма/описание — записать доход
➖ /withdraw сумма/описание — записать расход
📜 /history — посмотреть всю историю операций
   /history deposit — показать только доходы
   /history withdraw — показать только расходы
   /history last — показать последнюю операцию
   /history big — показать операцию с самой большой суммой
🎯 /add_goal сумма/goal/описание — создать финансовую цель
💳 /add_goal сумма/credit/описание — добавить долг
📋 /goals — посмотреть цели и долги
   /goals goal — показать только цели
   /goals credit — показать только долги

Сумма должна быть положительным целым числом.
В командах с несколькими аргументами разделяй их символом /.

Пример: /deposit 500/Зарплата""")


@dp.message(Command("profile"))
@dp.message(F.text == "👤 Профиль")
async def command_profile(message: Message):
    user = await profile(message.from_user.id)
    await message.answer(f"""
👤 ТВОЙ ПРОФИЛЬ

🪪 Имя: {user["full_name"]}
🔹 Имя пользователя: @{user["username"] or "не указано"}
💰 Баланс: {user["balance"]}
""")


@dp.message(Command("withdraw"))
async def command_withdraw(message: Message, command: CommandObject):
    usr = message.from_user
    if not command.args:
        await message.answer("""Для этой команды нужны сумма и описание.
Пример: /withdraw 10/Купил молоко""")
        return
    tran = command.args.split("/")
    if len(tran) < 2:
        await message.answer("""Не хватает аргументов. Укажи сумму и описание.
Пример: /withdraw 10/Купил молоко""")
        return
    if len(tran) > 2:
        await message.answer("""Слишком много аргументов. Нужны только сумма и описание.
Пример: /withdraw 10/Купил молоко""")
        return
    error = check_amount(tran[0])
    if error:
        await message.answer(error)
        return
    amount = int(tran[0])
    caption = tran[1].strip()
    if not caption:
        await message.answer("""Описание не может быть пустым.""")
        return
    user = await profile(message.from_user.id)
    if user["balance"] < amount:
        await message.answer("""На балансе недостаточно средств для этой операции.""")
        return
    else:
        if await make_transaction(caption, usr.id, amount, "withdraw"):
            await message.answer("✅ Расход успешно сохранён!")
        else:
            await message.answer("""Не удалось сохранить расход. Попробуй ещё раз.""")


@dp.message(Command("deposit"))
async def command_deposit(message: Message, command: CommandObject):
    usr = message.from_user
    if not command.args:
        await message.answer("""Для этой команды нужны сумма и описание.
Пример: /deposit 10/Продал молоко""")
        return
    tran = command.args.split("/")
    if len(tran) < 2:
        await message.answer("""Не хватает аргументов. Укажи сумму и описание.
Пример: /deposit 10/Продал молоко""")
        return
    if len(tran) > 2:
        await message.answer("""Слишком много аргументов. Нужны только сумма и описание.
Пример: /deposit 10/Продал молоко""")
        return
    error = check_amount(tran[0])
    if error:
        await message.answer(error)
        return
    amount = int(tran[0])
    caption = tran[1].strip()
    if not caption:
        await message.answer("""Описание не может быть пустым.""")
        return
    user = await profile(message.from_user.id) 
    if await make_transaction(caption, usr.id, amount, "deposit"):
        await message.answer("✅ Доход успешно сохранён!")
    else:
        await message.answer("""Не удалось сохранить доход. Попробуй ещё раз.""")


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
            await message.answer("""Неверный формат команды. Набери /help, чтобы посмотреть примеры.""")
            return
        elif data[0].lower() == "last":
            transictions = await get_last_tr(user.id)
            text += "🕘 Последняя операция\n"
        elif data[0].lower() == "big":
            transictions = await get_biggest_tr(user.id)
            text += "🏆 Самая крупная операция\n"
        elif data[0].lower() in ("withdraw", "deposit"):
            transictions = await get_tr_type(user.id, data[0].lower() )
            text += "➖ Расходы\n" if data[0].lower() == "withdraw" else "➕ Доходы\n"
        else:
            await message.answer("""Неверный формат команды. Набери /help, чтобы посмотреть примеры.""")
            return
    if not transictions:
        await message.answer("""История операций пока пуста.""")
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
        goals = await get_goals(user.id)
        text = """🎯 Твои цели и долги:\n"""
        empty = """Пока нет целей или долгов."""
    elif command.args.lower() in ("goal", "credit"):
        goal_type = command.args.lower()
        goals = await get_goals_type(user.id, goal_type)
        text = """🎯 Твои финансовые цели:\n""" if goal_type == "goal" else """💳 Твои долги:\n"""
        empty = """Пока нет финансовых целей.""" if goal_type == "goal" else """Пока нет долгов."""
    else:
        await message.answer("""Неверный формат команды. Набери /help, чтобы посмотреть примеры.""")
        return
    if not goals:
        await message.answer(empty)
        return
    for tr in goals:
        item_type = "Финансовая цель" if tr["type"] == "goal" else "Долг"
        progress_label = "Накоплено" if tr["type"] == "goal" else "Погашено"
        status_text = "Завершено" if tr["status"] else "В процессе"
        text += f"""

📌 Запись №{tr['id']} — {item_type}
📝 Описание: {tr['caption']}
💰 Общая сумма: {tr['amount']}
📈 {progress_label}: {tr['current_amount']}
📍 Статус: {status_text}
🕒 Дата создания: {tr['created_at']}"""
    await message.answer(text)


@dp.message(Command("add_goal"))
async def add_task(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Для команды нужны сумма, тип записи и описание.
Пример: /add_goal 5000/Аренда квартиры""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает аргументов. Укажи сумму и описание.
Пример: /add_goal 5000/Аренда квартиры""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Нужны только сумма  и описание.
Пример: /add_goal 5000/Аренда квартиры""")
        return
    error = check_amount(data[0])
    if error:
        await message.answer(error)
        return
    amount = int(data[0])
    caption = data[1].strip()
    if not caption:
        await message.answer("""Описание не может быть пустым.""")
        return
    if await create_goal(caption, amount, message.from_user.id):
        await message.answer("✅ Запись успешно создана!")
    else:
        await message.answer("""Не удалось создать запись. Проверь введённые данные.""")


@dp.message(Command("add_credit"))
async def add_task(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Для команды нужны сумма, тип записи и описание.
Пример: /add_credit 5000/Аренда квартиры""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает аргументов. Укажи сумму и описание.
Пример: /add_credit 5000/Аренда квартиры""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Нужны только сумма  и описание.
Пример: /add_credit 5000/Аренда квартиры""")
        return
    error = check_amount(data[0])
    if error:
        await message.answer(error)
        return
    amount = int(data[0])
    caption = data[1].strip()
    if not caption:
        await message.answer("""Описание не может быть пустым.""")
        return
    if await create_credit(caption, amount, message.from_user.id):
        await message.answer("✅ Запись успешно создана!")
    else:
        await message.answer("""Не удалось создать запись. Проверь введённые данные.""")













@dp.message(Command("pay_goal"))
async def pay(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Для команды нужны  id и сумма
Пример: /pay_goal 1/100""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает аргументов. Укажи id и  сумму.
Пример: /pay_goal 1/100""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Нужны только id и сумма.
Пример: /pay_goal 1/100""")
        return
    error = check_amount(data[1])
    if error:
        await message.answer(error)
        return
    user = await profile(message.from_user.id)
    amount = int(data[1])
    active = await get_active(message.from_user.id, data[0])
    if not active["is_active"]:
        await message.answer("Этот цель уже достигнут")
        return
    if active["amount"] < active["current_amount"] + amount:
        await message.answer("Слишком много денег!")
        return
    
    if await pay_goal(amount , data[0], message.from_user.id,):
        await message.answer("✅ Запись успешно создана!")
        if await get_status(message.from_user.id, data[0]):
            await message.answer("Вы успешно достигли своего целя")
    else:
        await message.answer("""Не удалось создать запись. Проверь введённые данные.""")



@dp.message(Command("repay"))
async def repayments(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("""Для команды нужны  id и сумма
Пример: /repay 1/100""")
        return
    data = command.args.split("/")
    if len(data) < 2:
        await message.answer("""Не хватает аргументов. Укажи id и  сумму.
Пример: /repay 1/100""")
        return
    if len(data) > 2:
        await message.answer("""Слишком много аргументов. Нужны только id и сумма.
Пример: /repay 1/100""")
        return
    error = check_amount(data[1])
    if error:
        await message.answer(error)
        return
    amount = int(data[1])
    active = await get_active(message.from_user.id, data[0])
    if not active["is_active"]:
        await message.answer("Этот цель уже достигнут")
        return
    if active["amount"] < active["current_amount"] + amount:
        await message.answer("Слишком много денег!")
        return
    user = await profile(message.from_user.id)
    
    if user["balance"] < amount:
        await message.answer("""На балансе недостаточно средств для этой операции.""")
        return
    if await repayments(amount , data[0], message.from_user.id,):
        await message.answer("✅ Запись успешно создана!")
    else:
        await message.answer("""Не удалось создать запись. Проверь введённые данные.""")





async def main():
    print("Bot started")
    await create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())