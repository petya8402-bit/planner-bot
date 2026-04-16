import asyncio
import json
import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command

TOKEN = "8383563078:AAE2Uko27_IvnAyZNoGodQebvSfeMUsFg_g"



bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"

# ================= JSON =================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= МЕНЮ =================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Мои задачи")],
        [KeyboardButton(text="📅 Ближайшие напоминания")],
        [KeyboardButton(text="🧹 Удалить все задачи")]
    ],
    resize_keyboard=True
)

# ================= СОСТОЯНИЯ =================
user_state = {}
temp_task = {}

# ================= ПРИОРИТЕТ =================
pr_map = {
    "low": "низкий",
    "medium": "средний",
    "high": "высокий"
}

# ================= UI =================
def task_keyboard(tasks):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for i, t in enumerate(tasks):
        status_icon = "✔" if t["status"] == "done" else "⏳"

        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} задача {i+1}",
                callback_data=f"toggle_{i}"
            )
        ])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="🔥 приоритет", callback_data=f"prio_menu_{i}"),
            InlineKeyboardButton(text="❌ удалить", callback_data=f"del_{i}")
        ])

    return kb


def priority_menu(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="низкий", callback_data=f"set_prio_low_{i}")],
        [InlineKeyboardButton(text="средний", callback_data=f"set_prio_medium_{i}")],
        [InlineKeyboardButton(text="высокий", callback_data=f"set_prio_high_{i}")]
    ])

# ================= START =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Я The_Planner 🤖\nПомогаю тебе планировать задачи и напоминания ✨",
        reply_markup=main_menu
    )

# ================= CALLBACK =================
@dp.callback_query()
async def callbacks(call: CallbackQuery):

    data = load_data()
    uid = str(call.from_user.id)

    if uid not in data:
        data[uid] = []

    # ===== УДАЛИТЬ =====
    if call.data.startswith("del_"):
        i = int(call.data.split("_")[1])

        if i < len(data[uid]):
            data[uid].pop(i)
            save_data(data)

        await call.message.edit_text("Задача удалена 🧹")
        return

    # ===== СТАТУС =====
    if call.data.startswith("toggle_"):
        i = int(call.data.split("_")[1])

        if i < len(data[uid]):
            task = data[uid][i]

            task["status"] = "done" if task["status"] == "active" else "active"
            save_data(data)

            await call.message.edit_text(
                f"✨ Статус обновлён:\n→ {task['status']}"
            )
        return

    # ===== ПРИОРИТЕТ МЕНЮ =====
    if call.data.startswith("prio_menu_"):
        i = int(call.data.split("_")[2])

        await call.message.edit_text(
            "Выбери приоритет задачи 👇",
            reply_markup=priority_menu(i)
        )
        return

    # ===== ПРИОРИТЕТ =====
    if call.data.startswith("set_prio_"):
        parts = call.data.split("_")
        level = parts[2]
        i = int(parts[3])

        if i < len(data[uid]):
            data[uid][i]["priority"] = level
            save_data(data)

            await call.message.edit_text(
                f"🔥 Приоритет: {pr_map[level]}"
            )
        return
    # ================= РОУТЕР =================
@dp.message()
async def router(message: Message):

    uid = message.from_user.id
    uid_s = str(uid)
    data = load_data()
    text = message.text

    # ===== ДОБАВИТЬ =====
    if text == "➕ Добавить задачу":
        user_state[uid] = "task"
        await message.answer("Напиши задачу ✍")
        return

    if user_state.get(uid) == "task":
        temp_task[uid] = {"text": text}
        user_state[uid] = "time"
        await message.answer("Время (HH:MM) или 'нет' ⏰")
        return

    if user_state.get(uid) == "time":
        temp_task[uid]["reminder"] = None if text.lower() == "нет" else text
        temp_task[uid]["status"] = "active"
        temp_task[uid]["priority"] = "low"

        data.setdefault(uid_s, []).append(temp_task[uid])
        save_data(data)

        user_state[uid] = None
        temp_task[uid] = None

        await message.answer("Задача добавлена ✨")
        return

    # ===== МОИ ЗАДАЧИ =====
    if text == "📋 Мои задачи":
        tasks = data.get(uid_s, [])

        if not tasks:
            await message.answer("У тебя пока нет задач 🤔")
            return

        out = "📋 Твои задачи ✨\n\n"

        for i, t in enumerate(tasks):
            st = "✔ выполнено" if t["status"] == "done" else "⏳ активно"
            pr = pr_map.get(t.get("priority", "low"))
            rem = f"⏰ {t['reminder']}" if t.get("reminder") else ""

            out += f"{i+1}. {t['text']} | {st} | 🔥 {pr} {rem}\n"

        await message.answer(out, reply_markup=task_keyboard(tasks))
        return

    # ===== УДАЛИТЬ ВСЕ =====
    if text == "🧹 Удалить все задачи":
        if uid_s not in data or not data[uid_s]:
            await message.answer("У тебя пока нет задач 🤔")
            return

        data[uid_s] = []
        save_data(data)

        await message.answer("Все задачи удалены 🧹✨")
        return

    # ===== БЛИЖАЙШИЕ =====
    if text == "📅 Ближайшие напоминания":
        tasks = [
            t for t in data.get(uid_s, [])
            if t.get("reminder") and t["status"] == "active"
        ]

        if not tasks:
            await message.answer("Нет активных напоминаний 🤔")
            return

        tasks.sort(key=lambda x: x["reminder"])

        out = "\n".join([f"⏰ {t['reminder']} — {t['text']}" for t in tasks])
        await message.answer(out)
        return

# ================= НАПОМИНАНИЯ =================
async def reminder_loop():
    while True:
        data = load_data()
        now = datetime.datetime.now().strftime("%H:%M")

        for uid, tasks in data.items():
            for t in tasks:
                if t.get("reminder") == now and t["status"] == "active":
                    try:
                        await bot.send_message(int(uid), f"⏰ {t['text']}")
                    except:
                        pass

        await asyncio.sleep(30)

# ================= RUN =================
async def main():
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())