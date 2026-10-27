import telebot
from telebot import types
import threading
import time
import os
from datetime import datetime, timedelta
from flask import Flask

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Хранилище активных таймеров пользователей: {user_id: [{'id':..., 'name':..., 'end_time':..., 'thread':...}]}
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
    btn_mines = types.KeyboardButton("💎 Рудники")
    btn_breeding = types.KeyboardButton("🥚 Выведение монстров")
    btn_guides = types.KeyboardButton("📖 Шпаргалка по комбинациям")
    btn_custom = types.KeyboardButton("⏱ Свой таймер")
    btn_my_timers = types.KeyboardButton("⏳ Мои активные таймеры")
    markup.add(btn_mines, btn_breeding, btn_guides, btn_custom, btn_my_timers)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я твой помощник по My Singing Monsters 🎵\n\nВыбери раздел в меню ниже:",
        reply_markup=get_main_keyboard()
    )

# РУДНИКИ
@bot.message_handler(func=lambda message: message.text == "💎 Рудники")
def mines_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💎 Обычный рудник (24 ч)", callback_data="mine_86400_Обычный рудник"),
        types.InlineKeyboardButton("💎 Улучшенный рудник (12 ч)", callback_data="mine_43200_Улучшенный рудник")
    )
    bot.send_message(message.chat.id, "Выбери тип рудника:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('mine_'))
def handle_mine_timer(call):
    data = call.data.split('_')
    seconds = int(data[1])
    mine_name = data[2]
    user_id = call.message.chat.id
    
    bot.answer_callback_query(call.id, text="Таймер запущен!")
    add_and_start_timer(user_id, mine_name, seconds)
    bot.send_message(user_id, f"✅ Таймер на **{mine_name}** ({seconds // 3600} ч) успешно запущен!", parse_mode="Markdown")

# ВЫВЕДЕНИЕ ПО ОСТРОВАМ
@bot.message_handler(func=lambda message: message.text == "🥚 Выведение монстров")
def breeding_islands_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌿 Растительный остров", callback_data="island_plant"),
        types.InlineKeyboardButton("❄️ Холодный остров", callback_data="island_cold"),
        types.InlineKeyboardButton("🌬️ Воздушный остров", callback_data="island_air"),
        types.InlineKeyboardButton("💧 Водный остров", callback_data="island_water"),
        types.InlineKeyboardButton("🌍 Остров Земли", callback_data="island_earth")
    )
    bot.send_message(message.chat.id, "Выбери остров:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('island_'))
def show_island_monsters(call):
    island = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if island == 'plant':
        markup.add(
            types.InlineKeyboardButton("Избалолист (24 ч)", callback_data="timer_86400_Избалолист"),
            types.InlineKeyboardButton("Вужас (36 ч)", callback_data="timer_129600_Вужас"),
            types.InlineKeyboardButton("Избалолист [Улучш.] (18 ч)", callback_data="timer_64800_Избалолист (улучш.)"),
            types.InlineKeyboardButton("Вужас [Улучш.] (27 ч)", callback_data="timer_97200_Вужас (улучш.)")
        )
        text = "🌿 **Растительный остров**:"
    elif island == 'cold':
        markup.add(
            types.InlineKeyboardButton("Тум (24 ч)", callback_data="timer_86400_Тум"),
            types.InlineKeyboardButton("Стовк (36 ч)", callback_data="timer_129600_Стовк")
        )
        text = "❄️ **Холодный остров**:"
    elif island == 'air':
        markup.add(
            types.InlineKeyboardButton("Шеппа (24 ч)", callback_data="timer_86400_Шеппа"),
            types.InlineKeyboardButton("Риф (36 ч)", callback_data="timer_129600_Риф")
        )
        text = "🌬️ **Воздушный остров**:"
    elif island == 'water':
        markup.add(
            types.InlineKeyboardButton("Раковица (24 ч)", callback_data="timer_86400_Раковица"),
            types.InlineKeyboardButton("Жуткий Блуб (36 ч)", callback_data="timer_129600_Жуткий Блуб")
        )
        text = "💧 **Водный остров**:"
    elif island == 'earth':
        markup.add(
            types.InlineKeyboardButton("Квариф (24 ч)", callback_data="timer_86400_Квариф"),
            types.InlineKeyboardButton("Клаблэф (36 ч)", callback_data="timer_129600_Клаблэф")
        )
        text = "🌍 **Остров Земли**:"
    else:
        return

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('timer_'))
def handle_breeding_timer(call):
    data = call.data.split('_')
    seconds = int(data[1])
    monster_name = data[2]
    user_id = call.message.chat.id
    
    bot.answer_callback_query(call.id, text="Таймер запущен!")
    add_and_start_timer(user_id, monster_name, seconds)
    bot.send_message(user_id, f"✅ Таймер на **{monster_name}** ({seconds // 3600} ч) запущен!", parse_mode="Markdown")

# СВОЙ ТАЙМЕР (С НАЗВАНИЕМ И ВРЕМЕНЕМ)
temp_timer_data = {}

@bot.message_handler(func=lambda message: message.text == "⏱ Свой таймер")
def ask_custom_name(message):
    msg = bot.send_message(message.chat.id, "✏️ Напиши, **на что** ты хочешь поставить таймер (например: *Пекарня* или *Улучшение замка*):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_custom_time)

def ask_custom_time(message):
    user_id = message.chat.id
    timer_name = message.text
    temp_timer_data[user_id] = timer_name
    
    msg = bot.send_message(user_id, f"⏱ Отлично: «**{timer_name}**». Теперь введи время в часах (можно дробное, например `12` или `1.5`):", parse_mode="Markdown")
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
        bot.send_message(user_id, "❌ Ошибка! Введи число (например, 12 или 2.5). Попробуй заново через меню.")

# УПРАВЛЕНИЕ АКТИВНЫМИ ТАЙМЕРАМИ
@bot.message_handler(func=lambda message: message.text == "⏳ Мои активные таймеры")
def show_my_timers(message):
    user_id = message.chat.id
    user_timers = active_timers.get(user_id, [])
    
    if not user_timers:
        bot.send_message(user_id, "📭 У тебя нет активных таймеров.")
        return
        
    text = "⏳ **Твои активные таймеры:**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    now = datetime.now()
    for t in user_timers:
        remaining = t['end_time'] - now
        if remaining.total_seconds() > 0:
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            time_str = f"{hours}ч {minutes}м"
        else:
            time_str = "Скоро завершится..."
            
        text += f"• **{t['name']}** — осталось примерно *{time_str}*\n"
        markup.add(types.InlineKeyboardButton(f"❌ Удалить: {t['name']}", callback_data=f"del_timer_{t['id']}"))
        
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_timer_'))
def delete_timer_callback(call):
    timer_id = int(call.data.split('_')[2])
    user_id = call.message.chat.id
    
    if user_id in active_timers:
        for t in active_timers[user_id]:
            if t['id'] == timer_id:
                active_timers[user_id].remove(t)
                bot.answer_callback_query(call.id, text="Таймер удален!")
                bot.edit_message_text("❌ Таймер был успешно удален.", call.message.chat.id, call.message.message_id)
                return
    bot.answer_callback_query(call.id, text="Таймер не найден.")

# ЛОГИКА ДОБАВЛЕНИЯ И ПОТОКОВ
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
    
    # Запускаем поток ожидания
    thread = threading.Thread(target=run_timer_thread, args=(user_id, timer_id, seconds, name))
    thread.start()

def run_timer_thread(user_id, timer_id, seconds, name):
    time.sleep(seconds)
    # Проверяем, не удалил ли пользователь таймер досрочно
    if user_id in active_timers:
        for t in active_timers[user_id]:
            if t['id'] == timer_id:
                active_timers[user_id].remove(t)
                bot.send_message(user_id, f"🔔 **Время вышло!** Твой таймер: «{name}» завершен!", parse_mode="Markdown")
                break

# ШПАРГАЛКИ
@bot.message_handler(func=lambda message: message.text == "📖 Шпаргалка по комбинациям")
def guides_islands_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌿 Растительный остров", callback_data="guide_plant"),
        types.InlineKeyboardButton("❄️ Холодный остров", callback_data="guide_cold"),
        types.InlineKeyboardButton("🌬️ Воздушный остров", callback_data="guide_air"),
        types.InlineKeyboardButton("💧 Водный остров", callback_data="guide_water"),
        types.InlineKeyboardButton("🌍 Остров Земли", callback_data="guide_earth")
    )
    bot.send_message(message.chat.id, "Выбери остров:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('guide_'))
def show_guide_content(call):
    island = call.data.split('_')[1]
    guides = {
        'plant': "🌿 **Растительный:**\n• Избалолист: Брюшок + Ти-Рокс\n• Вужас: Избалолист + Ти-Рокс\n• Сахабуш: Раковица + Смычорог",
        'cold': "❄️ **Холодный:**\n• Тум: Барабамень + Палезатор\n• Стовк: Тум + Палезатор",
        'air': "🌬️ **Воздушный:**\n• Шеппа: Зерноэть + Гупка\n• Риф: Шеппа + Гупка",
        'water': "💧 **Водный:**\n• Раковица: Усток + Рабуда\n• Жуткий Блуб: Раковица + Усток",
        'earth': "🌍 **Остров Земли:**\n• Квариф: Барабамень + Усток\n• Клаблэф: Квариф + Барабамень"
    }
    bot.edit_message_text(guides.get(island, "Нет данных"), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.start()
    print("Бот запущен...")
    bot.infinity_polling()
