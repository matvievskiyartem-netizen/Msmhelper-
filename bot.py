import telebot
from telebot import types
import threading
import time
import os
from datetime import datetime, timedelta
from flask import Flask

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Хранилище активных таймеров: {user_id: [{'id':..., 'name':..., 'end_time':...}]}
active_timers = {}

# ВЕБ-СЕРВЕР ДЛЯ RENDER
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ГЛАВНОЕ МЕНЮ
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_breeding = types.KeyboardButton("🥚 Выведение монстров")
    btn_mines = types.KeyboardButton("💎 Рудники")
    btn_guides = types.KeyboardButton("📖 Шпаргалка по комбинациям")
    btn_custom = types.KeyboardButton("⏱ Свой таймер")
    btn_my_timers = types.KeyboardButton("⏳ Мои активные таймеры")
    markup.add(btn_breeding, btn_mines, btn_guides, btn_custom, btn_my_timers)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "🎵 Привет! Я твой расширенный помощник по My Singing Monsters.\n\nВыбери нужный раздел в меню:",
        reply_markup=get_main_keyboard()
    )

# --- ВСЕ ОСТРОВА ДЛЯ ВЫВЕДЕНИЯ ---
ALL_ISLANDS = {
    "plant": "🌿 Растительный остров",
    "cold": "❄️ Холодный остров",
    "air": "🌬️ Воздушный остров",
    "water": "💧 Водный остров",
    "earth": "🌍 Остров Земли",
    "ethereal": "🌌 Эфирный остров",
    "workshop": "⚙️ Мастерская эфира",
    "faerie": "🧚 Остров Фей",
    "bone": "💀 Остров Костей",
    "light": "🕯️ Остров Света",
    "psychic": "🌀 Остров Психохилл",
    "seasonal": "🎃 Сезонный Остров",
    "oasis": "🌴 Остров Оазис",
    "cave": "🕯️ Остров Каверн"
}

# БАЗА МОНСТРОВ И ВРЕМЕНИ ВЫВЕДЕНИЯ (в секундах)
# Включает короткие и длинные таймеры для каждого острова
MONSTERS_DB = {
    'plant': [
        ("Пылесоц (12 мин)", 720), ("Зерноэть (30 мин)", 1800), ("Брюшок (1 ч)", 3600),
        ("Усток (2 ч)", 7200), ("Ти-Рокс (8 ч)", 28800), ("Избалолист (24 ч)", 86400),
        ("Вужас (36 ч)", 129600), ("Избалолист [Улучш.] (18 ч)", 64800), ("Вужас [Улучш.] (27 ч)", 97200)
    ],
    'cold': [
        ("Палезатор (30 мин)", 1800), ("Барабамень (1 ч)", 3600), ("Конвульсон (4 ч)", 14400),
        ("Тульт (8 ч)", 28800), ("Тум (24 ч)", 86400), ("Стовк (36 ч)", 129600)
    ],
    'air': [
        ("Гупка (30 мин)", 1800), ("Зерноэть (30 мин)", 1800), ("Регги (4 ч)", 14400),
        ("Палезатор (8 ч)", 28800), ("Шеппа (24 ч)", 86400), ("Риф (36 ч)", 129600)
    ],
    'water': [
        ("Усток (2 ч)", 7200), ("Рабуда (4 ч)", 14400), ("Ударник (8 ч)", 28800),
        ("Раковица (24 ч)", 86400), ("Жуткий Блуб (36 ч)", 129600)
    ],
    'earth': [
        ("Барабамень (1 ч)", 3600), ("Усток (2 ч)", 7200), ("Помпом (8 ч)", 28800),
        ("Квариф (24 ч)", 86400), ("Клаблэф (36 ч)", 129600)
    ],
    'ethereal': [
        ("Овулар (10 ч)", 36000), ("Ноготь (12 ч)", 43200), ("Сумрак (18 ч)", 64800),
        ("Жужжук (24 ч)", 86400), ("Басс (36 ч)", 129600)
    ],
    'workshop': [
        ("Медан (6 ч)", 21600), ("Пиккси (8 ч)", 28800), ("Бобруй (12 ч)", 43200),
        ("Синтез Сингл (18 ч)", 64800), ("Синтез Квад (36 ч)", 129600)
    ],
    'faerie': [
        ("Птицерога (4 ч)", 14400), ("Клювник (8 ч)", 28800), ("Флора (24 ч)", 86400)
    ],
    'bone': [
        ("Тралл (4 ч)", 14400), ("Череп (12 ч)", 43200), ("Канделябра (24 ч)", 86400)
    ],
    'light': [
        ("Светляк (4 ч)", 14400), ("Люмен (12 ч)", 43200), ("Сияние (24 ч)", 86400)
    ],
    'psychic': [
        ("Мента (6 ч)", 21600), ("Гипно (12 ч)", 43200), ("Психо (24 ч)", 86400)
    ],
    'seasonal': [
        ("Сезонный монстр (36 ч)", 129600)
    ],
    'oasis': [
        ("Оазис монстр 1 (8 ч)", 28800), ("Оазис монстр 2 (24 ч)", 86400)
    ],
    'cave': [
        ("Пещерный 1 (8 ч)", 28800), ("Пещерный 2 (24 ч)", 86400)
    ]
}

@bot.message_handler(func=lambda message: message.text == "🥚 Выведение монстров")
def breeding_islands_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"island_{code}"))
    bot.send_message(message.chat.id, "🌍 Выбери остров для выбора монстра:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('island_'))
def show_island_monsters(call):
    island_code = call.data.split('_')[1]
    monsters = MONSTERS_DB.get(island_code, [])
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for m_name, seconds in monsters:
        markup.add(types.InlineKeyboardButton(m_name, callback_data=f"bld_{seconds}_{m_name}"))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад к островам", callback_data="back_to_islands"))
    
    island_title = ALL_ISLANDS.get(island_code, "Остров")
    bot.edit_message_text(f"📍 **{island_title}** — выбери монстра:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_islands')
def back_to_islands(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"island_{code}"))
    bot.edit_message_text("🌍 Выбери остров для выбора монстра:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('bld_'))
def handle_breeding_timer_choice(call):
    parts = call.data.split('_', 2)
    seconds = int(parts[1])
    monster_name = parts[2]
    user_id = call.message.chat.id
    
    bot.answer_callback_query(call.id, text="Таймер запущен!")
    add_and_start_timer(user_id, monster_name, seconds)
    bot.send_message(user_id, f"✅ Таймер на выведение **{monster_name}** успешно запущен!", parse_mode="Markdown")

# --- РУДНИКИ ---
@bot.message_handler(func=lambda message: message.text == "💎 Рудники")
def mines_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💎 Обычный рудник (24 ч)", callback_data="mine_86400_Обычный рудник"),
        types.InlineKeyboardButton("💎 Улучшенный рудник (12 ч)", callback_data="mine_43200_Улучшенный рудник")
    )
    bot.send_message(message.chat.id, "💎 Выбери тип рудника:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('mine_'))
def handle_mine_timer(call):
    data = call.data.split('_')
    seconds = int(data[1])
    mine_name = data[2]
    user_id = call.message.chat.id
    
    bot.answer_callback_query(call.id, text="Рудник запущен!")
    add_and_start_timer(user_id, mine_name, seconds)
    bot.send_message(user_id, f"✅ Таймер на **{mine_name}** запущен!", parse_mode="Markdown")

# --- СВОЙ ТАЙМЕР ---
temp_timer_data = {}

@bot.message_handler(func=lambda message: message.text == "⏱ Свой таймер")
def ask_custom_name(message):
    msg = bot.send_message(message.chat.id, "✏️ Напиши, **на что** ты хочешь поставить таймер (например: *Пекарня*, *Улучшение замка*):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_custom_time)

def ask_custom_time(message):
    user_id = message.chat.id
    temp_timer_data[user_id] = message.text
    msg = bot.send_message(user_id, f"⏱ Отлично («**{message.text}**»). Теперь введи время в часах (можно дробное, например `12` или `1.5`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_custom_timer)

def save_custom_timer(message):
    user_id = message.chat.id
    try:
        hours = float(message.text.replace(',', '.'))
        seconds = int(hours * 3600)
        timer_name = temp_timer_data.get(user_id, "Свой таймер")
        
        add_and_start_timer(user_id, timer_name, seconds)
        bot.send_message(user_id, f"✅ Таймер «**{timer_name}**» на {hours} ч. успешно запущен!", parse_mode="Markdown")
    except ValueError:
        bot.send_message(user_id, "❌ Ошибка! Введи число (например, 12 или 2.5).")

# --- МОИ АКТИВНЫЕ ТАЙМЕРЫ И УДАЛЕНИЕ ---
@bot.message_handler(func=lambda message: message.text == "⏳ Мои активные таймеры")
def show_my_timers(message):
    user_id = message.chat.id
    user_timers = active_timers.get(user_id, [])
    
    if not user_timers:
        bot.send_message(user_id, "📭 У тебя нет активных таймеров.")
        return
        
    text = "⏳ **Твои активные таймеры в реальном времени:**\n\n"
    now = datetime.now()
    
    for t in user_timers:
        remaining = t['end_time'] - now
        if remaining.total_seconds() > 0:
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            time_str = f"{hours}ч {minutes}м"
        else:
            time_str = "Завершается..."
            
        text += f"• **{t['name']}** — осталось ~*{time_str}*\n"
    
    # Отдельная клавиатура с кнопками удаления каждого таймера
    markup = types.InlineKeyboardMarkup(row_width=1)
    for t in user_timers:
        markup.add(types.InlineKeyboardButton(f"❌ Удалить: {t['name']}", callback_data=f"del_tm_{t['id']}"))
        
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_tm_'))
def delete_timer_callback(call):
    timer_id = int(call.data.split('_')[2])
    user_id = call.message.chat.id
    
    removed = False
    if user_id in active_timers:
        for t in list(active_timers[user_id]):
            if t['id'] == timer_id:
                active_timers[user_id].remove(t)
                removed = True
                break
                
    if removed:
        bot.answer_callback_query(call.id, text="Таймер успешно удален!")
        bot.edit_message_text("❌ Таймер был удален из активных.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, text="Таймер не найден.")

# --- ПОЛНЫЕ ШПАРГАЛКИ ПО ВСЕМ ОСТРОВАМ ---
@bot.message_handler(func=lambda message: message.text == "📖 Шпаргалка по комбинациям")
def guides_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"g_island_{code}"))
    bot.send_message(message.chat.id, "📖 Выбери остров для просмотра комбинаций:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('g_island_'))
def show_guide_details(call):
    island_code = call.data.split('_')[2]
    
    guides_db = {
        'plant': "🌿 **Растительный остров:**\n• Избалолист: Брюшок + Ти-Рокс\n• Вужас: Избалолист + Ти-Рокс\n• Сахабуш: Раковица + Смычорог",
        'cold': "❄️ **Холодный остров:**\n• Тум: Барабамень + Палезатор\n• Стовк: Тум + Палезатор",
        'air': "🌬️ **Воздушный остров:**\n• Шеппа: Зерноэть + Гупка\n• Риф: Шеппа + Гупка",
        'water': "💧 **Водный остров:**\n• Раковица: Усток + Рабуда\n• Жуткий Блуб: Раковица + Усток",
        'earth': "🌍 **Остров Земли:**\n• Квариф: Барабамень + Усток\n• Клаблэф: Квариф + Барабамень",
        'ethereal': "🌌 **Эфирный остров:**\n• Жужжук: Овулар + Сумрак\n• Басс: Ноготь + Овулар",
        'workshop': "⚙️ **Мастерская эфира:**\n• Синтез сложных эфирных монстров требует стабильной башни и комбинации базовых элементов.",
        'faerie': "🧚 **Остров Фей:** Комбинации трехэлементных и четырехэлементных монстров.",
        'bone': "💀 **Остров Костей:** Редкие костяные монстры выводятся через комбинации базовых костяных элементов.",
        'light': "🕯️ **Остров Света:** Световые монстры.",
        'psychic': "🌀 **Остров Психохилл:** Психические монстры.",
        'seasonal': "🎃 **Сезонный Остров:** Доступен во время сезонных акций.",
        'oasis': "🌴 **Остров Оазис:** Огненные монстры.",
        'cave': "🕯️ **Остров Каверн:** Пещерные комбинации."
    }
    
    text = guides_db.get(island_code, "📖 Комбинации для этого острова скоро будут дополнены!")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад к списку островов", callback_data="back_to_guides"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_guides')
def back_to_guides(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"g_island_{code}"))
    bot.edit_message_text("📖 Выбери остров для просмотра комбинаций:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# --- ЛОГИКА ТАЙМЕРОВ ---
def add_and_start_timer(user_id, name, seconds):
    if user_id not in active_timers:
        active_timers[user_id] = []
        
    timer_id = int(time.time() * 1000)
    end_time = datetime.now() + timedelta(seconds=seconds)
    
    timer_obj = {
        'id': timer_id,
        'name': name,
        'end_time': end_time
    }
    
    active_timers[user_id].append(timer_obj)
    
    thread = threading.Thread(target=run_timer_thread, args=(user_id, timer_id, seconds, name))
    thread.start()

def run_timer_thread(user_id, timer_id, seconds, name):
    time.sleep(seconds)
    if user_id in active_timers:
        for t in active_timers[user_id]:
            if t['id'] == timer_id:
                active_timers[user_id].remove(t)
                bot.send_message(user_id, f"🔔 **Время вышло!** Твой таймер: «{name}» завершен!", parse_mode="Markdown")
                break

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.start()
    print("Бот со всеми островами и таймерами запущен...")
    bot.infinity_polling()
