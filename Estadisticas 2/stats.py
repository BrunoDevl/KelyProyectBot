import os
import sqlite3
import telebot
import matplotlib.pyplot as plt
import tempfile
import requests

TOKEN = '6063141885:AAGTehe_L0EbI4aaglCYHVzITMEp7sMFPyg'
AUTHORIZED_USER_ID = '5497883061'
DATABASES_FOLDER = 'databases'

bot = telebot.TeleBot(TOKEN)

def obtener_nombre_canal(canal_id):
    url = f'https://api.telegram.org/bot{TOKEN}/getChat?chat_id={canal_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['ok']:
            chat_info = data['result']
            return chat_info['title']
    return None

def crear_tabla_estadisticas_usuario(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS estadisticas_{user_id} (
            canal_id TEXT,
            num_subs INTEGER,
            num_subs_day INTEGER,
            num_unsubs_day INTEGER
        )
    ''')
    conn.commit()

def obtener_estadisticas_usuario(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT canal_id, num_subs, num_subs_day, num_unsubs_day
        FROM estadisticas_{user_id}
    ''')
    return cursor.fetchall()

def guardar_estadisticas_usuario(conn, user_id, estadisticas):
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM estadisticas_{user_id}')
    cursor.executemany(f'''
        INSERT INTO estadisticas_{user_id} (canal_id, num_subs, num_subs_day, num_unsubs_day)
        VALUES (?, ?, ?, ?)
    ''', estadisticas)
    conn.commit()

def generar_grafica(estadisticas):
    plt.figure(figsize=(10, 6))
    canales = [obtener_nombre_canal(canal_id) for canal_id, _, _, _ in estadisticas]
    num_subs = [num_subs for _, num_subs, _, _ in estadisticas]
    plt.bar(canales, num_subs)
    plt.xlabel('Canales')
    plt.ylabel('Número de subscriptores')
    plt.title('Estadísticas de Canales')
    temp_filename = tempfile.mktemp(suffix='.png')
    plt.savefig(temp_filename)
    return temp_filename

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = str(message.from_user.id)
    if user_id == AUTHORIZED_USER_ID:
        welcome_message = '''
        ¡Bienvenido al Bot de Estadísticas de Canales!

        Puedes utilizar los siguientes comandos:
        /stats - Obtener las estadísticas de los canales.
        /grafica - Generar una gráfica de las estadísticas.
        '''
        bot.reply_to(message, welcome_message)
    else:
        bot.reply_to(message, "Lo siento, no estás autorizado para utilizar este bot.")

@bot.message_handler(commands=['addchannel'])
def handle_add_channel(message):
    user_id = str(message.from_user.id)
    if user_id == AUTHORIZED_USER_ID:
        # Obtener el ID del canal a agregar
        if len(message.text.split()) == 2:
            channel_id = message.text.split()[1]
            # Realizar las operaciones necesarias para agregar el canal
            # Por ejemplo, puedes guardar el canal en la base de datos
            db_file = os.path.join(DATABASES_FOLDER, f'estadisticas_{user_id}.db')
            conn = sqlite3.connect(db_file)
            crear_tabla_estadisticas_usuario(conn, user_id)
            cursor = conn.cursor()
            cursor.execute(f'''
                INSERT INTO estadisticas_{user_id} (canal_id, num_subs, num_subs_day, num_unsubs_day)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, 0, 0, 0))
            conn.commit()
            conn.close()
            bot.reply_to(message, f"Canal {channel_id} agregado correctamente.")
        else:
            bot.reply_to(message, "Uso incorrecto del comando. Por favor, proporcione un ID de canal válido.")
    else:
        bot.reply_to(message, "Lo siento, no estás autorizado para utilizar este comando.")

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    user_id = str(message.from_user.id)
    if user_id == AUTHORIZED_USER_ID:
        db_file = os.path.join(DATABASES_FOLDER, f'estadisticas_{user_id}.db')
        conn = sqlite3.connect(db_file)
        crear_tabla_estadisticas_usuario(conn, user_id)
        estadisticas = obtener_estadisticas_usuario(conn, user_id)
        conn.close()

        if len(estadisticas) > 0:
            stats_message = "Estadísticas de Canales:\n\n"
            for canal_id, num_subs, num_subs_day, num_unsubs_day in estadisticas:
                nombre_canal = obtener_nombre_canal(canal_id)
                stats_message += f"Canal: {nombre_canal}\n"
                stats_message += f"Subscriptores actuales: {num_subs}\n"
                stats_message += f"Usuarios nuevos hoy: {num_subs_day}\n"
                stats_message += f"Usuarios que salieron hoy: {num_unsubs_day}\n"
                stats_message += "\n"
            bot.reply_to(message, stats_message)
        else:
            bot.reply_to(message, "No hay estadísticas disponibles.")
    else:
        bot.reply_to(message, "Lo siento, no estás autorizado para utilizar este comando.")

@bot.message_handler(commands=['grafica'])
def handle_grafica(message):
    user_id = str(message.from_user.id)
    if user_id == AUTHORIZED_USER_ID:
        db_file = os.path.join(DATABASES_FOLDER, f'estadisticas_{user_id}.db')
        conn = sqlite3.connect(db_file)
        crear_tabla_estadisticas_usuario(conn, user_id)
        estadisticas = obtener_estadisticas_usuario(conn, user_id)
        conn.close()

        if len(estadisticas) > 0:
            temp_filename = generar_grafica(estadisticas)
            with open(temp_filename, 'rb') as graph_file:
                bot.send_photo(message.chat.id, graph_file)
            os.remove(temp_filename)
        else:
            bot.reply_to(message, "No hay estadísticas disponibles.")
    else:
        bot.reply_to(message, "Lo siento, no estás autorizado para utilizar este comando.")

bot.polling()
