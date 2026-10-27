import telebot
from telebot import types
import threading
import time
import os
from datetime import datetime, timedelta
from flask import Flask

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Active user timers: {user_id: [{'id':..., 'name':..., 'end_time':...}]}
active_timers = {}

# WEB SERVER FOR RENDER
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# MAIN MENU
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_breeding = types.KeyboardButton("🥚 Breeding & Incubation")
    btn_mines = types.KeyboardButton("💎 Mines")
    btn_guides = types.KeyboardButton("📖 Breeding Guide")
    btn_custom = types.KeyboardButton("⏱ Custom Timer")
    btn_my_timers = types.KeyboardButton("⏳ My Active Timers")
    markup.add(btn_breeding, btn_mines, btn_guides, btn_custom, btn_my_timers)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "🎵 Welcome! Precise My Singing Monsters helper with Breeding & Incubation timers.\n\nChoose an option from the menu:",
        reply_markup=get_main_keyboard()
    )

ALL_ISLANDS = {
    "plant": "🌿 Plant Island",
    "cold": "❄️ Cold Island",
    "air": "🌬️ Air Island",
    "water": "💧 Water Island",
    "earth": "🌍 Earth Island",
    "ethereal": "🌌 Ethereal Island",
    "workshop": "⚙️ Ethereal Workshop",
    "faerie": "🧚 Faerie Island",
    "bone": "💀 Bone Island",
    "light": "🕯️ Light Island",
    "psychic": "🌀 Psychic Island",
    "faerie_s": "🪄 Shugabush Island"
}

# База данных монстров. Для каждого монстра храним нормальное время и улучшенное (Normal / Upgraded) в секундах.
# Формат: ("Monster Name", normal_seconds, upgraded_seconds)
MONSTERS_DB = {
    'plant': [
        ("Noggin", 5, 3),
        ("Toe Jammer", 30, 22),
        ("Mammott", 30, 22),
        ("Potbelly", 30, 22),
        ("Shrubb", 14400, 10800),
        ("Oaktopus", 21600, 16200),
        ("Furcorn", 28800, 21600),
        ("Drumpler", 1800, 1350),
        ("Fwog", 28800, 21600),
        ("Clamble", 43200, 32400),
        ("Bowgart", 43200, 32400),
        ("T-Rox", 28800, 21600),
        ("Entbrat", 86400, 64800),
        ("Ghazt", 129600, 97200)
    ],
    'cold': [
        ("Mammott", 30, 22),
        ("Toe Jammer", 30, 22),
        ("Oaktopus", 21600, 16200),
        ("Drumpler", 1800, 1350),
        ("Pango", 14400, 10800),
        ("Thumpies", 28800, 21600),
        ("Cybop", 28800, 21600),
        ("Deedge", 86400, 64800),
        ("Grumpyre", 129600, 97200)
    ],
    'air': [
        ("Potbelly", 30, 22),
        ("Mammott", 30, 22),
        ("Oaktopus", 21600, 16200),
        ("Pango", 14400, 10800),
        ("Cybop", 28800, 21600),
        ("Quibble", 43200, 32400),
        ("Riff", 86400, 64800),
        ("Reebro", 129600, 97200)
    ],
    'water': [
        ("Potbelly", 30, 22),
        ("Toe Jammer", 30, 22),
        ("Drumpler", 1800, 1350),
        ("Fwog", 28800, 21600),
        ("Clamble", 43200, 32400),
        ("Shellbeat", 86400, 64800),
        ("Bellowfish", 129600, 97200)
    ],
    'earth': [
        ("Noggin", 5, 3),
        ("Potbelly", 30, 22),
        ("Drumpler", 1800, 1350),
        ("Quibble", 43200, 32400),
        ("Stogg", 28800, 21600),
        ("Quarrister", 86400, 64800),
        ("Humbug", 129600, 97200)
    ],
    'ethereal': [
        ("Jeevode", 36000, 27000),
        ("Arackulele", 43200, 32400),
        ("Singe", 64800, 48600),
        ("Dragong", 86400, 64800),
        ("Whisp", 129600, 97200),
        ("Boodoo", 129600, 97200)
    ],
    'workshop': [
        ("Meeb", 600, 450),
        ("Whaack", 21600, 16200),
        ("Blasoom", 28800, 21600),
        ("Tyscorp", 43200, 32400),
        ("Single Synth", 64800, 48600),
        ("Double Synth", 86400, 64800),
        ("Triple Synth", 108000, 81000),
        ("Quad Synth", 129600, 97200)
    ],
    'faerie': [
        ("Wimmzies", 14400, 10800),
        ("Clavi Gnat", 28800, 21600),
        ("Pluckbill", 43200, 32400),
        ("Cantorell", 86400, 64800)
    ],
    'bone': [
        ("Clackula", 14400, 10800),
        ("Thrumble", 43200, 32400),
        ("Hawlo", 86400, 64800)
    ],
    'light': [
        ("Blow't", 14400, 10800),
        ("Spytrap", 43200, 32400),
        ("TooToo", 86400, 64800)
    ],
    'psychic': [
        ("Floot Fly", 21600, 16200),
        ("Clackula", 43200, 32400),
        ("Periscorp", 86400, 64800)
    ],
    'faerie_s': [
        ("Shugabush", 129600, 97200)
    ]
}

# Временное хранение выбора пользователя
user_selection = {}

@bot.message_handler(func=lambda message: message.text == "🥚 Breeding & Incubation")
def breeding_islands_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"island_{code}"))
    bot.send_message(message.chat.id, "🌍 Choose an island:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('island_'))
def show_island_monsters(call):
    island_code = call.data.split('_')[1]
    user_selection[call.message.chat.id] = {'island': island_code}
    
    monsters = MONSTERS_DB.get(island_code, [("Standard Monster", 86400, 64800)])
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for m_name, norm_sec, up_sec in monsters:
        markup.add(types.InlineKeyboardButton(m_name, callback_data=f"monster_{m_name}"))
    
    markup.add(types.InlineKeyboardButton("⬅️ Back to Islands", callback_data="back_to_islands"))
    
    island_title = ALL_ISLANDS.get(island_code, "Island")
    bot.edit_message_text(f"📍 **{island_title}** — select a monster:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_islands')
def back_to_islands(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"island_{code}"))
    bot.edit_message_text("🌍 Choose an island:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('monster_'))
def select_building_type(call):
    monster_name = call.data.split('_', 1)[1]
    user_id = call.message.chat.id
    
    if user_id not in user_selection:
        user_selection[user_id] = {}
    user_selection[user_id]['monster'] = monster_name
    
    # Шаг 2: Выбор постройки (Breeding Structure vs Nursery)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 Breeding Structure (Питомник)", callback_data="btype_breed"),
        types.InlineKeyboardButton("🥚 Nursery (Инкубатор)", callback_data="btype_nursery")
    )
    bot.edit_message_text(f"🎯 Monster: **{monster_name}**\n\nChoose building type:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('btype_'))
def select_upgrade_level(call):
    btype = call.data.split('_')[1]
    user_id = call.message.chat.id
    
    b_name = "Breeding Structure" if btype == 'breed' else "Nursery"
    user_selection[user_id]['btype'] = b_name
    
    # Шаг 3: Обычная или улучшенная (Normal vs Upgraded / Diamond)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚪ Normal (Обычная)", callback_data="lvl_normal"),
        types.InlineKeyboardButton("⭐ Upgraded / Diamond (Улучшенная -25%)", callback_data="lvl_upgraded")
    )
    bot.edit_message_text(f"🏗️ Building: **{b_name}**\n\nChoose upgrade level:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lvl_'))
def finalize_timer_setup(call):
    lvl = call.data.split('_')[1]
    user_id = call.message.chat.id
    
    data = user_selection.get(user_id, {})
    island_code = data.get('island', 'plant')
    monster_name = data.get('monster', 'Monster')
    btype = data.get('btype', 'Building')
    
    # Ищем секунды в базе
    monsters = MONSTERS_DB.get(island_code, [])
    norm_sec, up_sec = 86400, 64800
    for m, n_s, u_s in monsters:
        if m == monster_name:
            norm_sec, up_sec = n_s, u_s
            break
            
    seconds = up_sec if lvl == 'upgraded' else norm_sec
    lvl_str = "Upgraded" if lvl == 'upgraded' else "Normal"
    
    timer_title = f"{monster_name} ({btype} - {lvl_str})"
    
    bot.answer_callback_query(call.id, text="Timer started!")
    add_and_start_timer(user_id, timer_title, seconds)
    
    hours_left = seconds // 3600
    mins_left = (seconds % 3600) // 60
    time_text = f"{hours_left}h {mins_left}m" if hours_left > 0 else f"{mins_left}m"
    
    bot.edit_message_text(
        f"✅ Timer successfully started!\n\n• **{timer_title}**\n• Duration: **{time_text}**", 
        call.message.chat.id, 
        call.message.message_id, 
        parse_mode="Markdown"
    )

# --- MINES ---
@bot.message_handler(func=lambda message: message.text == "💎 Mines")
def mines_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💎 Plant Island Mine (24h)", callback_data="mine_86400_Plant Mine (24h)"),
        types.InlineKeyboardButton("💎 Upgraded Mine / Mirror (12h)", callback_data="mine_43200_Upgraded Mine (12h)")
    )
    bot.send_message(message.chat.id, "💎 Choose mine type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('mine_'))
def handle_mine_timer(call):
    data = call.data.split('_')
    seconds = int(data[1])
    mine_name = data[2]
    user_id = call.message.chat.id
    
    bot.answer_callback_query(call.id, text="Mine timer started!")
    add_and_start_timer(user_id, mine_name, seconds)
    bot.send_message(user_id, f"✅ Mine timer for **{mine_name}** started!", parse_mode="Markdown")

# --- CUSTOM TIMER ---
temp_timer_data = {}

@bot.message_handler(func=lambda message: message.text == "⏱ Custom Timer")
def ask_custom_name(message):
    msg = bot.send_message(message.chat.id, "✏️ Type **what** this timer is for (e.g., *Bakery*, *Castle Upgrade*):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_custom_time)

def ask_custom_time(message):
    user_id = message.chat.id
    temp_timer_data[user_id] = message.text
    msg = bot.send_message(user_id, f"⏱ Great («**{message.text}**»). Now enter the time in hours (decimals allowed, e.g., `12` or `1.5`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_custom_timer)

def save_custom_timer(message):
    user_id = message.chat.id
    try:
        hours = float(message.text.replace(',', '.'))
        seconds = int(hours * 3600)
        timer_name = temp_timer_data.get(user_id, "Custom Timer")
        
        add_and_start_timer(user_id, timer_name, seconds)
        bot.send_message(user_id, f"✅ Timer «**{timer_name}**» for {hours}h successfully started!", parse_mode="Markdown")
    except ValueError:
        bot.send_message(user_id, "❌ Error! Please enter a valid number (e.g., 12 or 2.5).")

# --- MY ACTIVE TIMERS & DELETION ---
@bot.message_handler(func=lambda message: message.text == "⏳ My Active Timers")
def show_my_timers(message):
    user_id = message.chat.id
    user_timers = active_timers.get(user_id, [])
    
    if not user_timers:
        bot.send_message(user_id, "📭 You have no active timers.")
        return
        
    text = "⏳ **Your Active Timers:**\n\n"
    now = datetime.now()
    
    for t in user_timers:
        remaining = t['end_time'] - now
        if remaining.total_seconds() > 0:
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = "Ending soon..."
            
        text += f"• **{t['name']}** — remaining ~*{time_str}*\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for t in user_timers:
        markup.add(types.InlineKeyboardButton(f"❌ Delete: {t['name']}", callback_data=f"del_tm_{t['id']}"))
        
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
        bot.answer_callback_query(call.id, text="Timer deleted successfully!")
        bot.edit_message_text("❌ Timer has been removed from active list.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, text="Timer not found.")

# --- BREEDING GUIDE ---
@bot.message_handler(func=lambda message: message.text == "📖 Breeding Guide")
def guides_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"g_island_{code}"))
    bot.send_message(message.chat.id, "📖 Choose an island to view breeding combinations:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('g_island_'))
def show_guide_details(call):
    island_code = call.data.split('_')[2]
    
    guides_db = {
        'plant': "🌿 **Plant Island Guide:**\n• Ghazt: Entbrat + T-Rox\n• Shugabush: Clamble + Bowgart\n• Entbrat: Bowgart + Potbelly",
        'cold': "❄️ **Cold Island Guide:**\n• Grumpyre: Deedge + Thumpies\n• Deedge: Thumpies + Pango",
        'air': "🌬️ **Air Island Guide:**\n• Reebro: Riff + Cybop\n• Riff: Cybop + Pango",
        'water': "💧 **Water Island Guide:**\n• Bellowfish: Shellbeat + Fwog\n• Shellbeat: Fwog + Drumpler",
        'earth': "🌍 **Earth Island Guide:**\n• Humbug: Quarrister + T-Rox\n• Quarrister: T-Rox + Noggin",
        'ethereal': "🌌 **Ethereal Island Guide:**\n• Whisp: Jeevode + Singe",
        'workshop': "⚙️ **Ethereal Workshop Guide:**\n• Synthesis requires stable towers.",
        'faerie': "🧚 **Faerie Island Guide:** Combine multi-element faerie monsters.",
        'bone': "💀 **Bone Island Guide:** Combine bone element monsters.",
        'light': "🕯️ **Light Island Guide:** Light element breeding combos.",
        'psychic': "🌀 **Psychic Island Guide:** Psychic element breeding combos.",
        'faerie_s': "🪄 **Shugabush Island:** Shugabush is bred on Plant Island (Clamble + Bowgart)."
    }
    
    text = guides_db.get(island_code, "📖 Breeding guide for this island coming soon.")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Back to Islands", callback_data="back_to_guides"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_guides')
def back_to_guides(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in ALL_ISLANDS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"g_island_{code}"))
    bot.edit_message_text("📖 Choose an island to view breeding combinations:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# --- TIMER THREAD LOGIC ---
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
                bot.send_message(user_id, f"🔔 **Time's up!** Your timer: «{name}» has finished!", parse_mode="Markdown")
                break

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.start()
    print("Bot with Building & Incubation timers is running...")
    bot.infinity_polling()
