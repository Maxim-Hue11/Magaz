import sqlite3
import telebot 
from dotenv import dotenv_values

# Создание объекта бота
config = dotenv_values('.env')
bot = telebot.TeleBot(config.get('Config.Token'))


#_________________


# Установка соединения с базой данных
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()

#_________________


# Создание таблицы товаров, если она не существует
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS products
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL)''')
conn.commit()


#_________________


# Создание таблицы пользователей, если она не существует
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL UNIQUE,
                balance INTEGER NOT NULL DEFAULT 0)''')
conn.commit()


#_________________


# Создание таблицы истории покупок, если она не существует
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS purchases
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                price INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users (id),
                FOREIGN KEY(product_id) REFERENCES products (id))''')
conn.commit()


#_________________


# Команда для просмотра списка товаров
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()

@bot.message_handler(commands=['products'])
def show_products(message):
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    
    if products:
        response = "Список товаров:\n"
        for product in products:
            response += f"{product[0]}. {product[1]} - {product[2]} руб.\n"
    else:
        response = "Товаров пока нет"
    
    bot.send_message(message.chat.id, response)


#_________________


# Команда для просмотра баланса пользователя
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()    

@bot.message_handler(commands=['balance'])
def show_balance(message):
    user_id = get_user_id(message.chat.id)
    if user_id:
        cursor.execute('SELECT balance FROM users WHERE id=?', (user_id,))
        balance = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"Ваш текущий баланс: {balance} руб.")
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы")


#_________________

# Команда для пополнения счета
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()        

@bot.message_handler(commands=['topup'])
def top_up_balance(message):
    amount = message.text.split()[1]
    try:
        amount = int(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректную сумму для пополнения")
        return
    
    user_id = get_user_id(message.chat.id)
    if user_id:
        cursor.execute('UPDATE users SET balance=balance+? WHERE id=?', (amount, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"Ваш баланс пополнен на {amount} руб.")
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы")

#_________________

# Команда для покупки товара
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()     

@bot.message_handler(commands=['buy'])
def buy_product(message):
    product_id = message.text.split()[1]
    try:
        product_id = int(product_id)
        if product_id <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректный номер товара")
        return
    
    cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
    product = cursor.fetchone()
    
    if product:
        user_id = get_user_id(message.chat.id)
        if user_id:
            cursor.execute('SELECT balance FROM users WHERE id=?', (user_id,))
            balance = cursor.fetchone()[0]
            
            if balance >= product[2]:
                cursor.execute('UPDATE users SET balance=balance-? WHERE id=?', (product[2], user_id))
                cursor.execute('INSERT INTO purchases (user_id, product_id, price) VALUES (?, ?, ?)',
                               (user_id, product[0], product[2]))
                conn.commit()
                bot.send_message(message.chat.id, f"Вы успешно приобрели товар '{product[1]}' за {product[2]} руб.")
            else:
                bot.send_message(message.chat.id, "На вашем счету недостаточно средств")
        else:
            bot.send_message(message.chat.id, "Вы не зарегистрированы")
    else:
        bot.send_message(message.chat.id, "Товар не найден")

#_________________

# Команда для просмотра истории покупок пользователя
conn = sqlite3.connect('Magaz.db')
cursor = conn.cursor()

@bot.message_handler(commands=['history'])
def show_history(message):
    user_id = get_user_id(message.chat.id)
    if user_id:
        cursor.execute('SELECT purchases.id, products.name, purchases.price, purchases.timestamp FROM purchases JOIN products ON purchases.product_id=products.id WHERE user_id=?',
                       (user_id,))
        purchases = cursor.fetchall()
        
        if purchases:
            response = "История ваших покупок:\n"
            for purchase in purchases:
                response += f"{purchase[0]}. {purchase[1]} - {purchase[2]} руб. ({purchase[3]})\n"
        else:
            response = "У вас пока нет покупок"
        
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы")

#_________________

# Вспомогательная функция для получения ID пользователя из базы данных
def get_user_id(chat_id):
    cursor.execute('SELECT id FROM users WHERE chat_id=?', (chat_id,))
    user_id = cursor.fetchone()
    return user_id[0] if user_id else None

#_________________

# Запуск бота
bot.polling(none_stop=True)