import telebot
from telebot import types
import threading
import time
import os

# Безопасный забор токена из настроек сервера
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_mines = types.KeyboardButton("💎 Рудники")
    btn_breeding = types.KeyboardButton("🥚 Выведение монстров")
    btn_guides = types.KeyboardButton("📖 Шпаргалка по комбинациям")
    btn_custom = types.KeyboardButton("⏱ Свой таймер")
    markup.add(btn_mines, btn_breeding, btn_guides, btn_custom)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я твой помощник по My Singing Monsters 🎵\n\nВыбери раздел в меню ниже:",
        reply_markup=get_main_keyboard()
    )

# --- РУДНИКИ ---
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
    bot.send_message(user_id, f"✅ Таймер на **{mine_name}** ({seconds // 3600} ч) запущен!", parse_mode="Markdown")
    
    thread = threading.Thread(target=run_timer, args=(user_id, seconds, f"💎 **{mine_name} готов!** Заходи и собирай алмазы."))
    thread.start()

# --- ВЫВЕДЕНИЕ ПО ОСТРОВАМ ---
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
    bot.send_message(user_id, f"✅ Таймер на **{monster_name}** ({seconds // 3600} ч) запущен!", parse_mode="Markdown")
    
    thread = threading.Thread(target=run_timer, args=(user_id, seconds, f"🥚 **{monster_name} выведен!** Пора забирать в инкубатор."))
    thread.start()

# --- СВОЙ ТАЙМЕР ---
@bot.message_handler(func=lambda message: message.text == "⏱ Свой таймер")
def ask_custom_time(message):
    msg = bot.send_message(message.chat.id, "Введи время выведения в часах (например: `12` или `8.5`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, set_custom_timer)

def set_custom_timer(message):
    try:
        hours = float(message.text.replace(',', '.'))
        seconds = int(hours * 3600)
        user_id = message.chat.id
        
        bot.send_message(user_id, f"✅ Таймер на **{hours} ч.** запущен!", parse_mode="Markdown")
        thread = threading.Thread(target=run_timer, args=(user_id, seconds, f"🔔 **Время вышло!** Твой таймер ({hours} ч) завершен!"))
        thread.start()
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи число (например, 12).")

# --- ШПАРГАЛКИ ---
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

def run_timer(user_id, delay, finish_message):
    time.sleep(delay)
    bot.send_message(user_id, finish_message, parse_mode="Markdown")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
