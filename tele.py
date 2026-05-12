import telebot

bot = telebot.TeleBot("8765941826:AAEcgCDGkX_QChWwRdb1sFhcm4t8NuovL3k")

@bot.message_handler(commands=['begin'])
def send_welcome(message):
    bot.reply_to(message, "my king! 👋")

bot.infinity_polling()