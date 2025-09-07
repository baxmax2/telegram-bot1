import random
import sqlite3
import math
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Предмети та фамільяри з ID та емодзі
ITEMS = {
    1: {"name": "Меч Бога Війни", "emoji": "⚔️"},
    2: {"name": "Щит Миру", "emoji": "🛡️"},
    3: {"name": "Магічна книга", "emoji": "📖"},
    4: {"name": "Еліксир правди", "emoji": "🧪"},
    5: {"name": "Кільце ", "emoji": "💍"},
    6: {"name": "Амулет", "emoji": "🧿"},
    7: {"name": "Скриня зла", "emoji": "📦"},
    8: {"name": "Ключ ", "emoji": "🔑"},
    9: {"name": "Плащ", "emoji": "🧥"},
    10: {"name": "Чоботи", "emoji": "🥾"},
    11: {"name": "???", "emoji": "",},
    12: {"name": "Кришталевий жезл", "emoji": "🪄", "raid_only": True},
    13: {"name": "Гільдійський Прапор", "emoji": "🏳️", "guild_only": True},
    14: {"name": "Корона Лідера", "emoji": "👑", "guild_only": True},
    15: {"name": "Мантія Слави", "emoji": "🧙‍♂️", "guild_only": True},
    16: {"name": "Бойовий Топірець", "emoji": "🪓"},
    17: {"name": "Лук Мисливця", "emoji": "🏹"},
    18: {"name": "Меч Самурая", "emoji": "🗡️"},
    19: {"name": "Палиця Шамана", "emoji": "🪃"},
    20: {"name": "Кинджал Асасина", "emoji": "🗡️"},
    21: {"name": "Сфера Влади", "emoji": "🔮"},
    22: {"name": "Плащ Невидимості", "emoji": "🧥"},
    23: {"name": "Сандалії Швидкості", "emoji": "👟"},
    24: {"name": "Перстень Сили", "emoji": "💪"},
    25: {"name": "Амулет Здоров'я", "emoji": "❤️"},
    26: {"name": "Книга Заклять", "emoji": "📚"},
    27: {"name": "Еліксир Мудрості", "emoji": "🧴"},
    28: {"name": "Щит Відваги", "emoji": "🛡️"},
    29: {"name": "Меч Світла", "emoji": "⚔️"},
    30: {"name": "Сфера Темряви", "emoji": "🌑"},

}
FAMILIARS = {
    101: {"name": "Фенікс", "emoji": "🔥"},
    102: {"name": "Дракон", "emoji": "🐉"},
    103: {"name": "Єдиноріг", "emoji": "🦄"},
    104: {"name": "Грифон", "emoji": "🦅"},
    105: {"name": "Кракен", "emoji": "🐙"},
    106: {"name": "Вовк", "emoji": "🐺"},
    107: {"name": "Кіт", "emoji": "🐱"},
    108: {"name": "Орел", "emoji": "🦅"},
    109: {"name": "Саламандра", "emoji": "🦎"},
    110: {"name": "Фея", "emoji": "🧚"},
    111: {"name": "Фінрір", "emoji": "🦊"},
    113: {"name": "Лев", "emoji": "🦁"},
    114: {"name": "Тигр", "emoji": "🐅"},
    115: {"name": "Ведмідь", "emoji": "🐻"},
    116: {"name": "Сова", "emoji": "🦉"},
    117: {"name": "Пантера", "emoji": "🐆"},
    118: {"name": "Змій", "emoji": "🐍"},
    119: {"name": "Кіт Баюн", "emoji": "🐈"},    
    120: {"name": "Тіньовий дух", "emoji": "👻", "raid_only": True},
    121: {"name": "Зоряний Фенікс", "emoji": "✨", "event_only": True},
    122: {"name": "Космічний Дракон", "emoji": "🌌", "event_only": True},
    123: {"name": "Легендарний Єдиноріг", "emoji": "🌈", "event_only": True},
    124: {"name": "Божественний Грифон", "emoji": "🌟", "event_only": True},
}

# Боси з ID
BOSSES = {
    1: {"name": "Темний Володар", "emoji": "😈"},
    2: {"name": "Крижаний Титан", "emoji": "❄️"},
    3: {"name": "Вогняний Лорд", "emoji": "🔥"},
    9999: {"name": "Легендарний Титан", "emoji": "👑"}
}

# Рідкості та їхні ймовірності
RARITIES = {
    "common": {"prob": 0.40, "damage": 5},
    "uncommon": {"prob": 0.25, "damage": 10},
    "rare": {"prob": 0.15, "damage": 30},
    "epic": {"prob": 0.10, "damage": 70},
    "legendary": {"prob": 0.05, "damage": 150},
    "mythic": {"prob": 0.03, "damage": 300},
    "divine": {"prob": 0.015, "damage": 500},
    "unreal": {"prob": 0.005, "damage": 1000}
}

# Титули за рівнями
TITLES = {
    1: "Новачок",
    5: "Інтерн",
    15: "Досвідчений",
    40: "Майстер",
    70: "Легенда",
    120: "Міфічний герой",
    200: "Божественний герой",
    300: "Неймовірний",
    450: "Лорд Легенд",
    700: "Епічний Володар",
    999: "Верховний Бог"
}

# Токен вашого бота та власник
TOKEN = os.getenv('TOKEN')
OWNER_ID = 6500735335
ADMINS = [6500735335]
# Зберігання стану івенту, рейду та гільдійських війн
EVENT = {"active": False, "type": None, "name": None, "end_time": None, "boss_hp": None, "boss_id": None}
GUILD_RAIDS = {}
GUILD_WARS = {}

# Ініціалізація бази даних SQLite
def init_db():
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        last_collect TEXT,
                        custom_title TEXT,
                        exp INTEGER DEFAULT 0,
                        bio TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS collections (
                        user_id INTEGER,
                        item_type TEXT,
                        item_id INTEGER,
                        rarity TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS familiars_level (
                        user_id INTEGER,
                        item_id INTEGER,
                        exp INTEGER DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS guilds (
                        guild_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        leader_id INTEGER,
                        co_leader_id INTEGER,
                        last_raid TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS guild_members (
                        guild_id INTEGER,
                        user_id INTEGER,
                        FOREIGN KEY(guild_id) REFERENCES guilds(guild_id),
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS guild_wars (
                        guild_id INTEGER,
                        opponent_id INTEGER,
                        damage INTEGER DEFAULT 0,
                        end_time TEXT,
                        boss_id INTEGER,
                        FOREIGN KEY(guild_id) REFERENCES guilds(guild_id)
                    )''')
        conn.commit()

# Функція для визначення рівня та титулу
def get_level_and_title(user_id):
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT exp, custom_title FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        exp = result[0] if result else 0
        level = math.floor(math.sqrt(exp))
        custom_title = result[1] if result and result[1] else None
        title = custom_title if custom_title else next((t for threshold, t in sorted(TITLES.items(), reverse=True) if level >= threshold), "Новачок")
        return level, title

# Функція для отримання рівнів фамільярів
def get_familiars_levels(user_id):
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT item_id, exp FROM familiars_level WHERE user_id = ?", (user_id,))
        familiars = c.fetchall()
        return {item_id: min(math.floor(math.sqrt(exp)), 999) for item_id, exp in familiars}

# Функція для пошуку user_id за нікнеймом або ID
def resolve_user_id(identifier, context):
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        identifier = identifier.lstrip('@')
        try:
            user_id = int(identifier)
            c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            return result[0] if result else None
        except ValueError:
            c.execute("SELECT user_id FROM users WHERE username = ?", (identifier,))
            result = c.fetchone()
            return result[0] if result else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or str(user_id)
    
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, exp, bio) VALUES (?, ?, ?, ?)", (user_id, username, 0, "Не встановлено"))
        conn.commit()
    
    keyboard = [
        [InlineKeyboardButton("📥 Зібрати", callback_data="collect")],
        [InlineKeyboardButton("📋 Інвентар", callback_data="inventory")],
        [InlineKeyboardButton("👤 Профіль", callback_data="profile")],
        [InlineKeyboardButton("🔍 Усі предмети", callback_data="all_items")],
        [InlineKeyboardButton("🏆 Топ гравців", callback_data="leaderboard")],
        [InlineKeyboardButton("🏰 Топ гільдій", callback_data="leaderboard_guild")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌟 **Ласкаво просимо до Колекціонера пригод!** 🌟\n\n"
        "Тут ти можеш збирати рідкісні предмети, виховувати фамільярів, битися з босами та створювати гільдії!\n\n"
        "**Основні команди:**\n"
        "📥 `/collect` — Зібрати скарби\n"
        "📋 `/inventory` — Твій інвентар\n"
        "👤 `/profile` — Твій профіль\n"
        "🔍 `/all_items` — Каталог усього\n"
        "🏆 `/leaderboard` — Топ героїв\n"
        "🏰 `/leaderboard_guild` — Топ гільдій\n"
        "⚔️ `/attack` — Атака на івент-боса\n"
        "🛡️ `/raid_attack <guild_id>` — Рейд у гільдії\n"
        "🏰 `/create_guild <назва>` — Створити гільдію\n"
        "🚪 `/join_guild <ID>` — Приєднатися\n"
        "📝 `/set_bio <текст>` — Змінити біо\n"
        "⚔️ `/guild_war <guild_id>` — Гільдійська війна\n"
        "📢 `/wow <текст>` — Глобальне сповіщення (адміни)\n"
        "🔧 `/admin_panel` — Панель адміна\n\n"
        "Готові до пригод? Почніть з `/collect`! 🚀",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    current_time = datetime.now()

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT last_collect FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result and result[0]:
            last_collect = datetime.fromisoformat(result[0])
            if (current_time - last_collect) < timedelta(hours=24):
                time_left = timedelta(hours=24) - (current_time - last_collect)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes = remainder // 60
                await update.effective_message.reply_text(
                    f"⏳ **Збір на кулдауні!**\nЗалишилось: *{hours} год {minutes} хв*.",
                    parse_mode='Markdown'
                )
                return

        collected_items = []
        if EVENT["active"] and EVENT["type"] == 3 and EVENT["end_time"] > current_time:
            await update.effective_message.reply_text("⚔️ **Бос-івент активний!** Використовуйте `/attack` для битви!", parse_mode='Markdown')
            return

        collect_count = 2 if EVENT["active"] and EVENT["type"] == 1 and random.random() < 0.7 else 1

        for _ in range(collect_count):
            rarity = random.choices(list(RARITIES.keys()), weights=[RARITIES[r]["prob"] for r in RARITIES], k=1)[0]
            available_items = [k for k, v in ITEMS.items() if not v.get("raid_only") and not v.get("guild_only")]
            available_familiars = [k for k, v in FAMILIARS.items() if not v.get("raid_only") and not v.get("event_only")]
            if random.random() < 0.5:
                item_id = random.choice(available_items)
                category = "предмет"
                name = ITEMS[item_id]["name"]
                emoji = ITEMS[item_id]["emoji"]
            else:
                item_id = random.choice(available_familiars)
                category = "фамільяр"
                name = FAMILIARS[item_id]["name"]
                emoji = FAMILIARS[item_id]["emoji"]
            collected_items.append((category, item_id, name, rarity, emoji))
            if category == "фамільяр":
                c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (user_id, item_id, 0))
            c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (user_id, category, item_id, rarity))
        
        c.execute("UPDATE users SET last_collect = ? WHERE user_id = ?", (current_time.isoformat(), user_id))
        c.execute("UPDATE users SET exp = exp + ? WHERE user_id = ?", (10 * collect_count, user_id))
        conn.commit()

    messages = [f"{emoji} **{category.capitalize()}** (*{rarity}*): {name}" for category, _, name, rarity, emoji in collected_items]
    await update.effective_message.reply_text(f"🎉 **Ви знайшли скарби!**\n\n" + "\n".join(messages), parse_mode='Markdown')

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT item_type, item_id, rarity FROM collections WHERE user_id = ?", (user_id,))
        collection = c.fetchall()
        familiars_levels = get_familiars_levels(user_id)

    if not collection:
        await update.effective_message.reply_text("😔 **Інвентар порожній.** Почніть з `/collect`!", parse_mode='Markdown')
        return

    items = [f"{ITEMS[row[1]]['emoji']} **{ITEMS[row[1]]['name']}** (*{row[2]}*)" for row in collection if row[0] == "предмет"]
    familiars = [f"{FAMILIARS[row[1]]['emoji']} **{FAMILIARS[row[1]]['name']}** (*{row[2]}*, рівень {familiars_levels.get(row[1], 1)})" 
                 for row in collection if row[0] == "фамільяр"]

    items_text = "\n".join(items) if items else "пусто"
    familiars_text = "\n".join(familiars) if familiars else "пусто"

    await update.effective_message.reply_text(
        f"📋 **Твій Інвентар** 📋\n\n"
        f"🗡️ **Предмети** ({len(items)}):\n{items_text}\n\n"
        f"🐉 **Фамільяри** ({len(familiars)}):\n{familiars_text}",
        parse_mode='Markdown'
    )

async def all_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
            # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
        with sqlite3.connect("collection_bot.db") as conn:
            c = conn.cursor()
            c.execute("SELECT item_type, item_id FROM collections WHERE user_id = ?", (user_id,))
            collection = c.fetchall()

        user_items = {row[1] for row in collection if row[0] == "предмет"}
        user_familiars = {row[1] for row in collection if row[0] == "фамільяр"}

        # ВИПРАВЛЕННЯ: видалили Markdown форматування
        items_list = [f"{v['emoji']} {v['name']} (ID: {k}) {'✅' if k in user_items else '❌'}" for k, v in ITEMS.items()]
        familiars_list = [f"{v['emoji']} {v['name']} (ID: {k}) {'✅' if k in user_familiars else '❌'}" for k, v in FAMILIARS.items()]

        items_text = "\n".join(items_list) if items_list else "Немає предметів"
        familiars_text = "\n".join(familiars_list) if familiars_list else "Немає фамільярів"

        # ВИПРАВЛЕННЯ: розділити повідомлення якщо занадто довге
        full_text = f"🔍 Каталог Усіх Скарбів 🔍\n\n🗡️ Предмети:\n{items_text}\n\n🐉 Фамільяри:\n{familiars_text}"
        
        # Перевіряємо довжину повідомлення (Telegram ліміт: 4096 символів)
        if len(full_text) > 4000:
            # Якщо задовге, розділяємо на частини
            await update.effective_message.reply_text(f"🔍 Каталог Усіх Скарбів 🔍\n\n🗡️ Предмети:\n{items_text}")
            await asyncio.sleep(1)
            await update.effective_message.reply_text(f"🐉 Фамільяри:\n{familiars_text}")
        else:
            await update.effective_message.reply_text(full_text)
                
    except Exception as e:
        print(f"Error in all_items function: {e}")
        if update.effective_message:
            await update.effective_message.reply_text("❌ Сталася помилка при отриманні каталогу!")

async def start_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 **Доступ заборонено!** Тільки для адмінів.", parse_mode='Markdown')
        return

    if len(context.args) != 3:
        await update.message.reply_text("❌ **Формат:** `/start_event <час у хвилинах> <назва> <тип 1-3>`", parse_mode='Markdown')
        return

    try:
        duration = int(context.args[0])
        event_name = context.args[1]
        event_type = int(context.args[2])
        if event_type not in [1, 2, 3]:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ **Помилка!** Час — число, тип — 1, 2 або 3.", parse_mode='Markdown')
        return

    EVENT["active"] = True
    EVENT["type"] = event_type
    EVENT["name"] = event_name
    EVENT["end_time"] = datetime.now() + timedelta(minutes=duration)
    EVENT["boss_hp"] = 100000 if event_type == 3 else None
    EVENT["boss_id"] = 9999 if event_type == 3 else None

    event_desc = {
        1: "📈 **Подвоєння скарбів!** Шанс отримати два предмети за `/collect`.",
        2: "🎁 **Подарунки для всіх!** Кожен отримує випадковий скарб.",
        3: f"⚔️ **Бос {BOSSES[9999]['name']} {BOSSES[9999]['emoji']}** (100,000 HP)! Атакуйте `/attack`."
    }

    keyboard = [[InlineKeyboardButton("⚔️ Атакувати боса", callback_data="attack_boss")]] if event_type == 3 else []
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user[0],
                text=f"🎉 **Івент '{event_name}' стартував!**\n\n{event_desc[event_type]}\n⏰ Триває до {EVENT['end_time'].strftime('%H:%M %d.%m')}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception:
            continue

    await update.message.reply_text(f"✅ **Івент '{event_name}' (тип {event_type}) запущено на {duration} хв!**", parse_mode='Markdown')

    if event_type == 2:
        with sqlite3.connect("collection_bot.db") as conn:
            c = conn.cursor()
            for user in users:
                user_id = user[0]
                rarity = random.choices(list(RARITIES.keys()), weights=[RARITIES[r]["prob"] for r in RARITIES], k=1)[0]
                available_items = [k for k, v in ITEMS.items() if not v.get("raid_only") and not v.get("guild_only")]
                available_familiars = [k for k, v in FAMILIARS.items() if not v.get("raid_only") and not v.get("event_only")]
                if random.random() < 0.5:
                    item_id = random.choice(available_items)
                    category = "предмет"
                    name = ITEMS[item_id]["name"]
                    emoji = ITEMS[item_id]["emoji"]
                else:
                    item_id = random.choice(available_familiars)
                    category = "фамільяр"
                    name = FAMILIARS[item_id]["name"]
                    emoji = FAMILIARS[item_id]["emoji"]
                c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (user_id, category, item_id, rarity))
                if category == "фамільяр":
                    c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (user_id, item_id, 0))
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎁 **Івент-подарунок '{event_name}':** {emoji} **{category.capitalize()}** (*{rarity}*): {name}",
                        parse_mode='Markdown'
                    )
                except Exception:
                    continue
            conn.commit()

    async def check_event_end():
        await asyncio.sleep(duration * 60)
        if EVENT["active"] and EVENT["end_time"] <= datetime.now():
            EVENT["active"] = False
            message = f"🏁 **Івент '{EVENT['name']}' завершено!**"
            if EVENT["type"] == 3 and EVENT["boss_hp"] > 0:
                message += f"\n{BOSSES[EVENT['boss_id']]['emoji']} **{BOSSES[EVENT['boss_id']]['name']}** вистояв ({EVENT['boss_hp']} HP)!"
            with sqlite3.connect("collection_bot.db") as conn:
                c = conn.cursor()
                c.execute("SELECT user_id FROM users")
                users = c.fetchall()
            for user in users:
                try:
                    await context.bot.send_message(chat_id=user[0], text=message, parse_mode='Markdown')
                except Exception:
                    continue
            EVENT.clear()
            EVENT.update({"active": False, "type": None, "name": None, "end_time": None, "boss_hp": None, "boss_id": None})

    asyncio.create_task(check_event_end())

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    current_time = datetime.now()

    if not EVENT["active"] or EVENT["type"] != 3 or EVENT["end_time"] <= current_time:
        await update.effective_message.reply_text("🚫 **Немає активного бос-івенту!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT last_collect FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result and result[0]:
            last_attack = datetime.fromisoformat(result[0])
            if (current_time - last_attack) < timedelta(minutes=5):
                time_left = timedelta(minutes=5) - (current_time - last_attack)
                minutes, seconds = divmod(time_left.seconds, 60)
                await update.effective_message.reply_text(
                    f"⏳ **Атака на кулдауні!**\nЗалишилось: *{minutes} хв {seconds} сек*.",
                    parse_mode='Markdown'
                )
                return

        level, _ = get_level_and_title(user_id)
        c.execute("SELECT item_id, rarity FROM collections WHERE user_id = ? AND item_type = ?", (user_id, "предмет"))
        items = c.fetchall()
        c.execute("SELECT item_id, rarity FROM collections WHERE user_id = ? AND item_type = ?", (user_id, "фамільяр"))
        familiars = c.fetchall()
        familiars_levels = get_familiars_levels(user_id)

        damage = 10 + level * 50
        for _, rarity in items:
            damage += RARITIES[rarity]["damage"]
        for item_id, rarity in familiars:
            damage += RARITIES[rarity]["damage"]
            damage += familiars_levels.get(item_id, 1)

        EVENT["boss_hp"] -= damage

        for item_id, _ in familiars:
            c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (user_id, item_id, 0))
            c.execute("UPDATE familiars_level SET exp = exp + ? WHERE user_id = ? AND item_id = ?", (damage, user_id, item_id))

        c.execute("UPDATE users SET exp = exp + ? WHERE user_id = ?", (damage // 10, user_id))
        c.execute("UPDATE users SET last_collect = ? WHERE user_id = ?", (current_time.isoformat(), user_id))

        if EVENT["boss_hp"] <= 0:
            EVENT["boss_hp"] = 0
            available_items = [k for k in ITEMS.keys() if not ITEMS[k].get("guild_only")]
            available_familiars = [k for k in FAMILIARS.keys()]
            item_id = random.choice(available_items + available_familiars)
            category = "предмет" if item_id in ITEMS else "фамільяр"
            name = ITEMS[item_id]["name"] if category == "предмет" else FAMILIARS[item_id]["name"]
            emoji = ITEMS[item_id]["emoji"] if category == "предмет" else FAMILIARS[item_id]["emoji"]
            rarity = random.choices(list(RARITIES.keys()), weights=[RARITIES[r]["prob"] for r in RARITIES], k=1)[0]
            c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (user_id, category, item_id, rarity))
            if category == "фамільяр":
                c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (user_id, item_id, 0))
            conn.commit()
            await update.effective_message.reply_text(
                f"🎉 **{BOSSES[EVENT['boss_id']]['name']} {BOSSES[EVENT['boss_id']]['emoji']} переможений!**\n\n"
                f"🏆 **Нагорода:** {emoji} **{category.capitalize()}** (*{rarity}*): {name}\n"
                f"🐉 Фамільяри набрали *{damage} EXP*.",
                parse_mode='Markdown'
            )
            with sqlite3.connect("collection_bot.db") as conn:
                c = conn.cursor()
                c.execute("SELECT user_id FROM users")
                users = c.fetchall()
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user[0],
                        text=f"🏁 **Івент '{EVENT['name']}' завершено!**\n{BOSSES[EVENT['boss_id']]['emoji']} **{BOSSES[EVENT['boss_id']]['name']}** переможений!",
                        parse_mode='Markdown'
                    )
                except Exception:
                    continue
            EVENT["active"] = False
        else:
            conn.commit()
            await update.effective_message.reply_text(
                f"⚔️ **Атака завдала {damage} шкоди {BOSSES[EVENT['boss_id']]['name']} {BOSSES[EVENT['boss_id']]['emoji']}!**\n\n"
                f"❤️ Залишилось HP: *{EVENT['boss_hp']}*\n🐉 Фамільяри набрали *{damage} EXP*.",
                parse_mode='Markdown'
            )

async def raid_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    current_time = datetime.now()

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ **Формат:** `/raid_attack <guild_id>`", parse_mode='Markdown')
        return

    guild_id = int(context.args[0])
    if guild_id not in GUILD_RAIDS or GUILD_RAIDS[guild_id]["end_time"] <= current_time:
        await update.message.reply_text("🚫 **Немає активного рейду в гільдії!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        user_guild = c.fetchone()
        if not user_guild or user_guild[0] != guild_id:
            await update.message.reply_text(f"🚫 **Ви не член гільдії ID {guild_id}!**", parse_mode='Markdown')
            return

        c.execute("SELECT last_collect FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result and result[0]:
            last_attack = datetime.fromisoformat(result[0])
            if (current_time - last_attack) < timedelta(minutes=5):
                time_left = timedelta(minutes=5) - (current_time - last_attack)
                minutes, seconds = divmod(time_left.seconds, 60)
                await update.message.reply_text(
                    f"⏳ **Атака на кулдауні!**\nЗалишилось: *{minutes} хв {seconds} сек*.",
                    parse_mode='Markdown'
                )
                return

        level, _ = get_level_and_title(user_id)
        c.execute("SELECT item_id, rarity FROM collections WHERE user_id = ? AND item_type = ?", (user_id, "предмет"))
        items = c.fetchall()
        c.execute("SELECT item_id, rarity FROM collections WHERE user_id = ? AND item_type = ?", (user_id, "фамільяр"))
        familiars = c.fetchall()
        familiars_levels = get_familiars_levels(user_id)

        damage = 10 + level * 50
        for _, rarity in items:
            damage += RARITIES[rarity]["damage"]
        for item_id, rarity in familiars:
            damage += RARITIES[rarity]["damage"]
            damage += familiars_levels.get(item_id, 1)

        GUILD_RAIDS[guild_id]["boss_hp"] -= damage
        boss_id = GUILD_RAIDS[guild_id]["boss_id"]

        for item_id, _ in familiars:
            c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (user_id, item_id, 0))
            c.execute("UPDATE familiars_level SET exp = exp + ? WHERE user_id = ? AND item_id = ?", (damage, user_id, item_id))

        c.execute("UPDATE users SET exp = exp + ? WHERE user_id = ?", (damage // 10, user_id))
        c.execute("UPDATE users SET last_collect = ? WHERE user_id = ?", (current_time.isoformat(), user_id))

        if guild_id in GUILD_WARS:
            c.execute("UPDATE guild_wars SET damage = damage + ? WHERE guild_id = ?", (damage, guild_id))

        if GUILD_RAIDS[guild_id]["boss_hp"] <= 0:
            GUILD_RAIDS[guild_id]["boss_hp"] = 0
            available_items = [k for k in ITEMS.keys()]
            available_familiars = [k for k in FAMILIARS.keys() if not FAMILIARS[k].get("event_only")]
            item_id = random.choice(available_items + available_familiars)
            category = "предмет" if item_id in ITEMS else "фамільяр"
            name = ITEMS[item_id]["name"] if category == "предмет" else FAMILIARS[item_id]["name"]
            emoji = ITEMS[item_id]["emoji"] if category == "предмет" else FAMILIARS[item_id]["emoji"]
            rarity = random.choices(list(RARITIES.keys()), weights=[RARITIES[r]["prob"] for r in RARITIES], k=1)[0]
            c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (user_id, category, item_id, rarity))
            if category == "фамільяр":
                c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (user_id, item_id, 0))
            conn.commit()
            await update.message.reply_text(
                f"🎉 **{BOSSES[boss_id]['name']} {BOSSES[boss_id]['emoji']} переможений!**\n\n"
                f"🏆 **Нагорода:** {emoji} **{category.capitalize()}** (*{rarity}*): {name}\n"
                f"🐉 Фамільяри набрали *{damage} EXP*.",
                parse_mode='Markdown'
            )
            c.execute("SELECT user_id FROM guild_members WHERE guild_id = ?", (guild_id,))
            members = c.fetchall()
            for member in members:
                try:
                    await context.bot.send_message(
                        chat_id=member[0],
                        text=f"🏁 **Рейд завершено!**\n{BOSSES[boss_id]['emoji']} **{BOSSES[boss_id]['name']}** переможений!",
                        parse_mode='Markdown'
                    )
                except Exception:
                    continue
            del GUILD_RAIDS[guild_id]
        else:
            conn.commit()
            await update.message.reply_text(
                f"⚔️ **Атака завдала {damage} шкоди {BOSSES[boss_id]['name']} {BOSSES[boss_id]['emoji']}!**\n\n"
                f"❤️ Залишилось HP: *{GUILD_RAIDS[guild_id]['boss_hp']}*\n🐉 Фамільяри набрали *{damage} EXP*.",
                parse_mode='Markdown'
            )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
            # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
        username = update.effective_user.username or str(user_id)
        
        print(f"Debug: Processing profile for user_id: {user_id}, username: {username}")

        with sqlite3.connect("collection_bot.db") as conn:
            c = conn.cursor()
            
            # Перевіряємо чи існує таблиця users
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not c.fetchone():
                await update.effective_message.reply_text("❌ Помилка бази даних: таблиця users не існує!")
                return
            
            # Перевіряємо чи існує користувач
            c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
            user_exists = c.fetchone()[0] > 0
            
            print(f"Debug: User exists: {user_exists}")
            
            if not user_exists:
                # Створюємо нового користувача
                c.execute("INSERT INTO users (user_id, username, exp, bio, last_collect) VALUES (?, ?, ?, ?, ?)", 
                         (user_id, username, 0, "Не встановлено", datetime.now().isoformat()))
                conn.commit()
                print(f"Debug: Created new user with id: {user_id}")
            
            # Оновлюємо username
            c.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
            
            # Отримуємо дані профілю
            c.execute("SELECT exp, bio, custom_title FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            
            print(f"Debug: Database result: {result}")
            
            if result:
                exp = result[0] if result[0] is not None else 0
                bio = result[1] if result[1] is not None else "Не встановлено"
                custom_title = result[2]
                level = math.floor(math.sqrt(exp)) if exp > 0 else 0
                
                # Знаходимо відповідний титул
                title = "Новачок"
                for threshold, title_name in sorted(TITLES.items(), reverse=True):
                    if level >= threshold:
                        title = title_name
                        break
                
                if custom_title:
                    title = custom_title
                    
                print(f"Debug: exp={exp}, level={level}, title={title}, bio={bio}")
                
                # ВИПРАВЛЕННЯ: використовуємо effective_message замість message
                await update.effective_message.reply_text(
                    f"👤 Профіль Колеціонера 👤\n\n"
                    f"-------------------\n"
                    f"🆔 ID: {user_id}\n"
                    f"-------------------\n"
                    f"📛 Ім'я: {username}\n"
                    f"-------------------\n"
                    f"🏆 Титул: {title}\n"
                    f"-------------------\n"
                    f"📊 Рівень: {level}\n"
                    f"-------------------\n"
                    f"⭐ EXP: {exp}\n"
                    f"-------------------\n"
                    f"📜 Біо: {bio}"
                )
            else:
                await update.effective_message.reply_text("❌ Помилка: не вдалося отримати дані профілю!")
                
    except Exception as e:
        print(f"Error in profile function: {e}")
        if update.effective_message:
            await update.effective_message.reply_text("❌ Сталася помилка при отриманні профілю!")

async def title_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titles_text = "\n".join([f"🏆 **{title}** (Рівень {level})" for level, title in sorted(TITLES.items())])
    await update.message.reply_text(f"📜 **Список Титулів:**\n\n{titles_text}", parse_mode='Markdown')

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with sqlite3.connect("collection_bot.db") as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, username, exp FROM users WHERE exp > 0 ORDER BY exp DESC LIMIT 10")
            top_users = c.fetchall()

        if not top_users:
            await update.effective_message.reply_text("🏆 Рейтинг порожній! Почніть збирати скарби з /collect.")
            return

        leaderboard_text = "\n".join(
            f"{i+1}. @{row[1] if row[1] else row[0]} — Рівень {math.floor(math.sqrt(row[2]))} (EXP: {row[2]})" 
            for i, row in enumerate(top_users)
        )
        
        await update.effective_message.reply_text(f"🏆 Топ-10 Героїв:\n\n{leaderboard_text}")
                
    except Exception as e:
        print(f"Error in leaderboard function: {e}")
        if update.effective_message:
            await update.effective_message.reply_text("❌ Сталася помилка при отриманні рейтингу!")

async def leaderboard_guild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id, name FROM guilds")
        guilds = c.fetchall()
        
        guild_levels = []
        for guild_id, guild_name in guilds:
            c.execute("SELECT SUM(exp) FROM users JOIN guild_members ON users.user_id = guild_members.user_id WHERE guild_id = ?", (guild_id,))
            total_exp = c.fetchone()[0] or 0
            guild_levels.append((guild_name, math.floor(math.sqrt(total_exp))))
        
        guild_levels = sorted(guild_levels, key=lambda x: x[1], reverse=True)[:10]

    if not guild_levels:
        await update.effective_message.reply_text("🏰 **Рейтинг гільдій порожній!** Створіть першу.", parse_mode='Markdown')
        return

    leaderboard_text = "\n".join(
        f"{i+1}. **{name}** — Сумарний рівень: *{level}*" for i, (name, level) in enumerate(guild_levels)
    )
    await update.effective_message.reply_text(f"🏰 **Топ-10 Гільдій:**\n\n{leaderboard_text}", parse_mode='Markdown')

async def set_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    if not context.args:
        await update.message.reply_text("❌ **Формат:** `/set_bio <текст>`", parse_mode='Markdown')
        return

    bio = " ".join(context.args)
    if len(bio) > 50:
        await update.message.reply_text("❌ **Біо не може бути довшим за 50 символів!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET bio = ? WHERE user_id = ?", (bio, user_id))
        conn.commit()

    await update.message.reply_text(f"📝 **Біо оновлено:** *{bio}*", parse_mode='Markdown')

async def create_guild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    if not context.args:
        await update.message.reply_text("❌ **Формат:** `/create_guild <назва>`", parse_mode='Markdown')
        return

    guild_name = " ".join(context.args)
    if len(guild_name) > 50:
        await update.message.reply_text("❌ **Назва гільдії не може бути довшою за 50 символів!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        if c.fetchone():
            await update.message.reply_text("🚫 **Ви вже в гільдії!** Вийдіть спочатку: `/leave_guild`", parse_mode='Markdown')
            return

        c.execute("INSERT INTO guilds (name, leader_id) VALUES (?, ?)", (guild_name, user_id))
        guild_id = c.lastrowid
        c.execute("INSERT INTO guild_members (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        conn.commit()

    await update.message.reply_text(f"🏰 **Гільдія '{guild_name}' (ID: {guild_id}) створена!** Ви — лідер. 👑", parse_mode='Markdown')

async def join_guild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ **Формат:** `/join_guild <ID>`", parse_mode='Markdown')
        return

    guild_id = int(context.args[0])
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        if c.fetchone():
            await update.message.reply_text("🚫 **Ви вже в гільдії!** Вийдіть спочатку: `/leave_guild`", parse_mode='Markdown')
            return

        c.execute("SELECT name FROM guilds WHERE guild_id = ?", (guild_id,))
        guild = c.fetchone()
        if not guild:
            await update.message.reply_text(f"❌ **Гільдія з ID {guild_id} не існує!**", parse_mode='Markdown')
            return

        c.execute("INSERT INTO guild_members (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        conn.commit()

    await update.message.reply_text(f"🚪 **Ви приєдналися до '{guild[0]}' (ID: {guild_id})!** 🎉", parse_mode='Markdown')

async def leave_guild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        guild = c.fetchone()
        if not guild:
            await update.message.reply_text("🚫 **Ви не в гільдії!**", parse_mode='Markdown')
            return

        guild_id = guild[0]
        c.execute("SELECT leader_id, co_leader_id FROM guilds WHERE guild_id = ?", (guild_id,))
        guild_info = c.fetchone()
        if guild_info[0] == user_id:
            await update.message.reply_text("🚫 **Лідер не може покинути гільдію!**", parse_mode='Markdown')
            return

        c.execute("DELETE FROM guild_members WHERE user_id = ?", (user_id,))
        if guild_info[1] == user_id:
            c.execute("UPDATE guilds SET co_leader_id = NULL WHERE guild_id = ?", (guild_id,))
        conn.commit()

    await update.message.reply_text("🚶 **Ви покинули гільдію!** 😔", parse_mode='Markdown')

async def set_co_leader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    if not context.args:
        await update.message.reply_text("❌ **Формат:** `/set_co_leader <нікнейм/ID>`", parse_mode='Markdown')
        return

    co_leader_id = resolve_user_id(context.args[0], context)
    if not co_leader_id:
        await update.message.reply_text("❌ **Користувач не знайдений!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        guild = c.fetchone()
        if not guild:
            await update.message.reply_text("🚫 **Ви не в гільдії!**", parse_mode='Markdown')
            return

        guild_id = guild[0]
        c.execute("SELECT leader_id FROM guilds WHERE guild_id = ?", (guild_id,))
        leader_id = c.fetchone()
        if not leader_id or leader_id[0] != user_id:
            await update.message.reply_text("🚫 **Тільки лідер може призначити со-лідера!**", parse_mode='Markdown')
            return

        c.execute("SELECT user_id FROM guild_members WHERE guild_id = ? AND user_id = ?", (guild_id, co_leader_id))
        if not c.fetchone():
            await update.message.reply_text("❌ **Користувач не є членом гільдії!**", parse_mode='Markdown')
            return

        c.execute("UPDATE guilds SET co_leader_id = ? WHERE guild_id = ?", (co_leader_id, guild_id))
        conn.commit()

    await update.message.reply_text(f"👑 **Користувач (ID: {co_leader_id}) призначений со-лідером!**", parse_mode='Markdown')

async def guild_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id, name FROM guilds")
        guilds = c.fetchall()

    if not guilds:
        await update.message.reply_text("🏰 **Гільдій немає!** Створіть свою: `/create_guild`", parse_mode='Markdown')
        return

    guild_text = "\n".join([f"🏰 **{g[1]}** (ID: {g[0]})" for g in guilds])
    await update.message.reply_text(f"📜 **Список Гільдій:**\n\n{guild_text}", parse_mode='Markdown')

async def guild_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        guild = c.fetchone()
        if not guild:
            await update.message.reply_text("🚫 **Ви не в гільдії!**", parse_mode='Markdown')
            return

        guild_id = guild[0]
        c.execute("SELECT name, leader_id, co_leader_id FROM guilds WHERE guild_id = ?", (guild_id,))
        guild_info = c.fetchone()
        c.execute("SELECT user_id, username FROM guild_members JOIN users ON guild_members.user_id = users.user_id WHERE guild_id = ?", (guild_id,))
        members = c.fetchall()

    members_text = "\n".join([f"👤 **@{m[1] if m[1] else m[0]}**{' (Лідер)' if m[0] == guild_info[1] else ' (Со-лідер)' if m[0] == guild_info[2] else ''}" for m in members])
    await update.message.reply_text(f"👥 **Гільдія '{guild_info[0]}' (ID: {guild_id}):**\n\n{members_text}", parse_mode='Markdown')

async def start_raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    current_time = datetime.now()

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        guild = c.fetchone()
        if not guild:
            await update.message.reply_text("🚫 **Ви не в гільдії!**", parse_mode='Markdown')
            return

        guild_id = guild[0]
        c.execute("SELECT leader_id, co_leader_id, last_raid FROM guilds WHERE guild_id = ?", (guild_id,))
        guild_info = c.fetchone()
        if user_id not in [guild_info[0], guild_info[1]]:
            await update.message.reply_text("🚫 **Тільки лідер або со-лідер може запустити рейд!**", parse_mode='Markdown')
            return

        if guild_info[2]:
            last_raid = datetime.fromisoformat(guild_info[2])
            if (current_time - last_raid) < timedelta(hours=3):
                time_left = timedelta(hours=3) - (current_time - last_raid)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes = remainder // 60
                await update.message.reply_text(f"⏳ **Рейд на кулдауні!** Залишилось: *{hours} год {minutes} хв*.", parse_mode='Markdown')
                return

        boss_id = random.choice([k for k in BOSSES.keys() if k != 9999])
        GUILD_RAIDS[guild_id] = {
            "end_time": current_time + timedelta(minutes=30),
            "boss_hp": 100000,
            "boss_id": boss_id
        }
        c.execute("UPDATE guilds SET last_raid = ? WHERE guild_id = ?", (current_time.isoformat(), guild_id))
        conn.commit()

        c.execute("SELECT user_id FROM guild_members WHERE guild_id = ?", (guild_id,))
        members = c.fetchall()

    for member in members:
        try:
            await context.bot.send_message(
                chat_id=member[0],
                text=f"🛡️ **Рейд-бос {BOSSES[boss_id]['name']} {BOSSES[boss_id]['emoji']} з'явився!**\n\n"
                     f"❤️ HP: *100,000*\n⚔️ Атакуйте: `/raid_attack {guild_id}`\n⏰ Триває до {GUILD_RAIDS[guild_id]['end_time'].strftime('%H:%M %d.%m')}",
                parse_mode='Markdown'
            )
        except Exception:
            continue

    await update.message.reply_text(f"🛡️ **Рейд запущено для гільдії ID {guild_id}!** Бийте боса {BOSSES[boss_id]['name']}.", parse_mode='Markdown')

    async def check_raid_end():
        await asyncio.sleep(30 * 60)
        if guild_id in GUILD_RAIDS and GUILD_RAIDS[guild_id]["end_time"] <= datetime.now():
            boss_hp = GUILD_RAIDS[guild_id]["boss_hp"]
            boss_name = BOSSES[GUILD_RAIDS[guild_id]["boss_id"]]["name"]
            boss_emoji = BOSSES[GUILD_RAIDS[guild_id]["boss_id"]]["emoji"]
            with sqlite3.connect("collection_bot.db") as conn:
                c = conn.cursor()
                c.execute("SELECT user_id FROM guild_members WHERE guild_id = ?", (guild_id,))
                members = c.fetchall()
            message = f"🏁 **Рейд завершено!**\n{boss_emoji} **{boss_name}** {'вистояв (*' + str(boss_hp) + '* HP)' if boss_hp > 0 else 'переможений!'}"
            for member in members:
                try:
                    await context.bot.send_message(chat_id=member[0], text=message, parse_mode='Markdown')
                except Exception:
                    continue
            del GUILD_RAIDS[guild_id]

    asyncio.create_task(check_raid_end())

async def guild_war(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
        # ЦЕЙ БЛОК ⬇️
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            await update.message.reply_text("⚠️ **Спочатку використай /start**")
            return
    # ЦЕЙ БЛОК ⬆️
    current_time = datetime.now()

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ **Формат:** `/guild_war <guild_id>`", parse_mode='Markdown')
        return

    opponent_guild_id = int(context.args[0])
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        guild = c.fetchone()
        if not guild:
            await update.message.reply_text("🚫 **Ви не в гільдії!**", parse_mode='Markdown')
            return

        guild_id = guild[0]
        c.execute("SELECT leader_id, co_leader_id FROM guilds WHERE guild_id = ?", (guild_id,))
        guild_info = c.fetchone()
        if user_id not in [guild_info[0], guild_info[1]]:
            await update.message.reply_text("🚫 **Тільки лідер або со-лідер може викликати на війну!**", parse_mode='Markdown')
            return

        c.execute("SELECT name FROM guilds WHERE guild_id = ?", (opponent_guild_id,))
        opponent_guild = c.fetchone()
        if not opponent_guild:
            await update.message.reply_text(f"❌ **Гільдія з ID {opponent_guild_id} не існує!**", parse_mode='Markdown')
            return

        if guild_id == opponent_guild_id:
            await update.message.reply_text("🚫 **Не можна воювати з собою!**", parse_mode='Markdown')
            return

        c.execute("SELECT guild_id FROM guild_wars WHERE guild_id IN (?, ?)", (guild_id, opponent_guild_id))
        if c.fetchone():
            await update.message.reply_text("🚫 **Одна з гільдій уже в війні!**", parse_mode='Markdown')
            return

        c.execute("SELECT name FROM guilds WHERE guild_id = ?", (guild_id,))
        guild_name = c.fetchone()[0]
        c.execute("SELECT user_id FROM guild_members WHERE guild_id = ?", (guild_id,))
        guild_members = [m[0] for m in c.fetchall()]
        c.execute("SELECT user_id FROM guild_members WHERE guild_id = ?", (opponent_guild_id,))
        opponent_members = [m[0] for m in c.fetchall()]

        boss_id = random.choice([k for k in BOSSES.keys() if k != 9999])
        GUILD_RAIDS[guild_id] = {
            "end_time": current_time + timedelta(minutes=60),
            "boss_hp": 100000,
            "boss_id": boss_id
        }
        GUILD_RAIDS[opponent_guild_id] = {
            "end_time": current_time + timedelta(minutes=60),
            "boss_hp": 100000,
            "boss_id": boss_id
        }
        GUILD_WARS[guild_id] = {
            "opponent_id": opponent_guild_id,
            "damage": 0,
            "end_time": current_time + timedelta(minutes=60),
            "boss_id": boss_id
        }
        GUILD_WARS[opponent_guild_id] = {
            "opponent_id": guild_id,
            "damage": 0,
            "end_time": current_time + timedelta(minutes=60),
            "boss_id": boss_id
        }
        c.execute("INSERT INTO guild_wars (guild_id, opponent_id, damage, end_time, boss_id) VALUES (?, ?, ?, ?, ?)",
                  (guild_id, opponent_guild_id, 0, current_time.isoformat(), boss_id))
        c.execute("INSERT INTO guild_wars (guild_id, opponent_id, damage, end_time, boss_id) VALUES (?, ?, ?, ?, ?)",
                  (opponent_guild_id, guild_id, 0, current_time.isoformat(), boss_id))
        conn.commit()

    for member_id in guild_members + opponent_members:
        target_guild_id = guild_id if member_id in guild_members else opponent_guild_id
        try:
            await context.bot.send_message(
                chat_id=member_id,
                text=f"⚔️ **Гільдійська війна: '{guild_name}' (ID: {guild_id}) vs '{opponent_guild[0]}' (ID: {opponent_guild_id})!**\n\n"
                     f"Бийте боса {BOSSES[boss_id]['name']} {BOSSES[boss_id]['emoji']} (`/raid_attack {target_guild_id}`)\n"
                     f"⏰ Триває до {GUILD_WARS[guild_id]['end_time'].strftime('%H:%M %d.%m')}",
                parse_mode='Markdown'
            )
        except Exception:
            continue

    await update.message.reply_text(f"⚔️ **Війна між ID {guild_id} та ID {opponent_guild_id} розпочата!**", parse_mode='Markdown')

    async def check_war_end():
        await asyncio.sleep(60 * 60)
        if guild_id in GUILD_WARS and GUILD_WARS[guild_id]["end_time"] <= datetime.now():
            with sqlite3.connect("collection_bot.db") as conn:
                c = conn.cursor()
                c.execute("SELECT guild_id, name FROM guilds WHERE guild_id IN (?, ?)", (guild_id, opponent_guild_id))
                guilds = c.fetchall()
                guild_name = next(g[1] for g in guilds if g[0] == guild_id)
                opponent_name = next(g[1] for g in guilds if g[0] == opponent_guild_id)
                c.execute("SELECT guild_id, damage FROM guild_wars WHERE guild_id IN (?, ?)", (guild_id, opponent_guild_id))
                damages = c.fetchall()

                guild_damage = next(d[1] for d in damages if d[0] == guild_id)
                opponent_damage = next(d[1] for d in damages if d[0] == opponent_guild_id)
                winner_id = guild_id if guild_damage > opponent_damage else opponent_guild_id if opponent_damage > guild_damage else None
                winner_name = guild_name if guild_damage > opponent_damage else opponent_name if opponent_damage > guild_damage else None

                message = f"🏁 **Гільдійська війна завершена!**\n\n"
                if winner_id:
                    item_id = random.choice([12, 13, 14])
                    rarity = "legendary"
                    c.execute("SELECT user_id FROM guild_members WHERE guild_id = ?", (winner_id,))
                    members = c.fetchall()
                    for member in members:
                        c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (member[0], "предмет", item_id, rarity))
                    conn.commit()
                    message += f"🏆 **Перемогла '{winner_name}' (ID: {winner_id})!**\n"
                    message += f"🎁 **Нагорода:** {ITEMS[item_id]['emoji']} **{ITEMS[item_id]['name']}** (*{rarity}*) для всіх членів!"
                else:
                    message += "🤝 **Нічия!**"

                c.execute("SELECT user_id FROM guild_members WHERE guild_id IN (?, ?)", (guild_id, opponent_guild_id))
                members = c.fetchall()
                for member in members:
                    try:
                        await context.bot.send_message(chat_id=member[0], text=message, parse_mode='Markdown')
                    except Exception:
                        continue
                
                c.execute("DELETE FROM guild_wars WHERE guild_id IN (?, ?)", (guild_id, opponent_guild_id))
                conn.commit()
            
            if guild_id in GUILD_RAIDS:
                del GUILD_RAIDS[guild_id]
            if opponent_guild_id in GUILD_RAIDS:
                del GUILD_RAIDS[opponent_guild_id]
            if guild_id in GUILD_WARS:
                del GUILD_WARS[guild_id]
            if opponent_guild_id in GUILD_WARS:
                del GUILD_WARS[opponent_guild_id]

    asyncio.create_task(check_war_end())

async def give_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("🚫 **Доступ тільки для власника бота!**", parse_mode='Markdown')
        return

    if len(context.args) != 3 or context.args[1] not in ["предмет", "фамільяр"] or context.args[2] not in RARITIES:
        await update.message.reply_text("❌ **Формат:** `/give_item <нікнейм/ID> <предмет/фамільяр> <рідкість>`", parse_mode='Markdown')
        return

    target_user_id = resolve_user_id(context.args[0], context)
    if not target_user_id:
        await update.message.reply_text("❌ **Користувач не знайдений!**", parse_mode='Markdown')
        return

    category = context.args[1]
    rarity = context.args[2]
    items = ITEMS if category == "предмет" else FAMILIARS
    available_items = [k for k, v in items.items() if not v.get("raid_only") and not v.get("guild_only") and not v.get("event_only")]
    if not available_items:
        await update.message.reply_text("❌ **Немає доступних предметів для видачі!**", parse_mode='Markdown')
        return
    item_id = random.choice(available_items)
    name = items[item_id]["name"]
    emoji = items[item_id]["emoji"]

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_user_id,))
        c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (target_user_id, category, item_id, rarity))
        if category == "фамільяр":
            c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (target_user_id, item_id, 0))
        conn.commit()

    await update.message.reply_text(f"✅ **Видано:** {emoji} **{category.capitalize()}** (*{rarity}*): {name} (ID: {target_user_id})", parse_mode='Markdown')
    try:
        await context.bot.send_message(chat_id=target_user_id, text=f"🎁 **Отримано:** {emoji} **{category.capitalize()}** (*{rarity}*): {name}", parse_mode='Markdown')
    except Exception:
        pass

async def create_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("🚫 **Доступ тільки для власника бота!**", parse_mode='Markdown')
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ **Формат:** `/create_title <нікнейм/ID> <титул>`", parse_mode='Markdown')
        return

    target_user_id = resolve_user_id(context.args[0], context)
    if not target_user_id:
        await update.message.reply_text("❌ **Користувач не знайдений!**", parse_mode='Markdown')
        return

    custom_title = " ".join(context.args[1:])
    if len(custom_title) > 50:
        await update.message.reply_text("❌ **Титул не може бути довшим за 50 символів!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_user_id,))
        c.execute("UPDATE users SET custom_title = ? WHERE user_id = ?", (custom_title, target_user_id))
        conn.commit()

    await update.message.reply_text(f"✅ **Титул '{custom_title}' встановлено для ID {target_user_id}!**", parse_mode='Markdown')
    try:
        await context.bot.send_message(chat_id=target_user_id, text=f"🏆 **Новий титул:** *{custom_title}*!", parse_mode='Markdown')
    except Exception:
        pass

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 **Доступ тільки для адмінів!**", parse_mode='Markdown')
        return

    if len(context.args) != 2 or not context.args[1].isdigit():
        await update.message.reply_text("❌ **Формат:** `/set_level <нікнейм/ID> <exp>`", parse_mode='Markdown')
        return

    target_user_id = resolve_user_id(context.args[0], context)
    if not target_user_id:
        await update.message.reply_text("❌ **Користувач не знайдений!**", parse_mode='Markdown')
        return

    exp = int(context.args[1])
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_user_id,))
        c.execute("UPDATE users SET exp = ? WHERE user_id = ?", (exp, target_user_id))
        conn.commit()

    level = math.floor(math.sqrt(exp))
    await update.message.reply_text(f"✅ **Встановлено {exp} EXP для ID {target_user_id}.** Рівень: *{level}*", parse_mode='Markdown')
    try:
        await context.bot.send_message(chat_id=target_user_id, text=f"🔧 **Ваш рівень оновлено:** *{level}* (EXP: {exp})", parse_mode='Markdown')
    except Exception:
        pass

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 2 or not context.args[1].isdigit():
        await update.message.reply_text("❌ **Формат:** `/gift <нікнейм/ID> <item_id>`", parse_mode='Markdown')
        return

    target_user_id = resolve_user_id(context.args[0], context)
    if not target_user_id:
        await update.message.reply_text("❌ **Користувач не знайдений!**", parse_mode='Markdown')
        return

    if target_user_id == user_id:
        await update.message.reply_text("🚫 **Не можна дарувати собі!**", parse_mode='Markdown')
        return

    item_id = int(context.args[1])
    if item_id not in ITEMS and item_id not in FAMILIARS:
        await update.message.reply_text("❌ **Неправильний ID скарбу!**", parse_mode='Markdown')
        return

    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT item_type, rarity FROM collections WHERE user_id = ? AND item_id = ? LIMIT 1", (user_id, item_id))
        item = c.fetchone()
        if not item:
            await update.message.reply_text("❌ **У вас немає цього скарбу!**", parse_mode='Markdown')
            return

        category, rarity = item
        c.execute("DELETE FROM collections WHERE user_id = ? AND item_id = ? AND rarity = ? LIMIT 1", (user_id, item_id, rarity))
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_user_id,))
        c.execute("INSERT INTO collections (user_id, item_type, item_id, rarity) VALUES (?, ?, ?, ?)", (target_user_id, category, item_id, rarity))
        if category == "фамільяр":
            c.execute("INSERT OR IGNORE INTO familiars_level (user_id, item_id, exp) VALUES (?, ?, ?)", (target_user_id, item_id, 0))
        conn.commit()

    name = ITEMS[item_id]["name"] if category == "предмет" else FAMILIARS[item_id]["name"]
    emoji = ITEMS[item_id]["emoji"] if category == "предмет" else FAMILIARS[item_id]["emoji"]
    await update.message.reply_text(f"🎁 **Подарунок надіслано:** {emoji} **{category.capitalize()}** (*{rarity}*): {name} для ID {target_user_id}", parse_mode='Markdown')
    try:
        await context.bot.send_message(chat_id=target_user_id, text=f"🎁 **Отримано подарунок:** {emoji} **{category.capitalize()}** (*{rarity}*): {name}", parse_mode='Markdown')
    except Exception:
        pass

async def wow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 **Доступ тільки для адмінів!**", parse_mode='Markdown')
        return

    if not context.args:
        await update.message.reply_text("❌ **Формат:** `/wow <текст>`", parse_mode='Markdown')
        return

    message = " ".join(context.args)
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()

    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=f"📢 **Глобальне сповіщення:**\n\n{message}", parse_mode='Markdown')
        except Exception:
            continue

    await update.message.reply_text(f"✅ **Сповіщення надіслано:** *{message}*", parse_mode='Markdown')

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 **Доступ тільки для адмінів!**", parse_mode='Markdown')
        return

    keyboard = [
        [InlineKeyboardButton("🎁 Видача предмета", callback_data="admin_give_item")],
        [InlineKeyboardButton("🏆 Створити титул", callback_data="admin_create_title")],
        [InlineKeyboardButton("🔧 Встановити рівень", callback_data="admin_set_level")],
        [InlineKeyboardButton("📢 Сповіщення", callback_data="admin_wow")],
        [InlineKeyboardButton("🎉 Запустити івент", callback_data="admin_start_event")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 **Адмін-Панель:**\n\nОберіть дію:", reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    commands = {
        "attack_boss": attack,
        "collect": collect,
        "inventory": inventory,
        "profile": profile,
        "all_items": all_items,
        "leaderboard": leaderboard,
        "leaderboard_guild": leaderboard_guild
    }

    if query.data in commands:
        await commands[query.data](update, context)
    elif query.data.startswith("admin_"):
        command = query.data.split("_")[1]
        await query.message.reply_text(f"🔧 **Введіть команду:** `/{command} <параметри>`", parse_mode='Markdown')

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or str(user_id)
    
    with sqlite3.connect("collection_bot.db") as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, exp, bio) VALUES (?, ?, ?, ?)", (user_id, username, 0, "Не встановлено"))
        c.execute("UPDATE users SET exp = exp + 1, username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_message = "⚠️ **Виникла помилка!** Спробуйте ще раз або зверніться до адміна."
    if update:
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_message, parse_mode='Markdown')
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer(error_message, show_alert=True)

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("collect", collect))
    app.add_handler(CommandHandler("inventory", inventory))
    app.add_handler(CommandHandler("all_items", all_items))
    app.add_handler(CommandHandler("start_event", start_event))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("raid_attack", raid_attack))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("title_list", title_list))
    app.add_handler(CommandHandler("create_guild", create_guild))
    app.add_handler(CommandHandler("join_guild", join_guild))
    app.add_handler(CommandHandler("leave_guild", leave_guild))
    app.add_handler(CommandHandler("set_co_leader", set_co_leader))
    app.add_handler(CommandHandler("guild_list", guild_list))
    app.add_handler(CommandHandler("guild_members", guild_members))
    app.add_handler(CommandHandler("start_raid", start_raid))
    app.add_handler(CommandHandler("give_item", give_item))
    app.add_handler(CommandHandler("create_title", create_title))
    app.add_handler(CommandHandler("set_level", set_level))
    app.add_handler(CommandHandler("wow", wow))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("leaderboard_guild", leaderboard_guild))
    app.add_handler(CommandHandler("set_bio", set_bio))
    app.add_handler(CommandHandler("guild_war", guild_war))
    app.add_handler(CommandHandler("admin_panel", admin_panel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error_handler)
    
    app.run_polling()

if __name__ == "__main__":

    main()








