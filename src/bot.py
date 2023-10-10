
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler
import argparse
import logging
import json
import re

SPELLING_FILE = "spellings.json"
SPELLING_PATTERN = r'\[(.*?)\]'
ALPHABET_PATTERN = r'[^a-zA-Z\s]+'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Handler for when the /start command is received
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Enter '/help' to see a list of commands.")

# Handler for when the /help command is received
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="TODO..list of commands")

# Handler for when the /add_spell command is received
async def add_spell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Supply a sentence containing the word to add surrounding by [square] brackets.")
        return

    words = " ".join(context.args)

    print(f"Words = {words}")

    matches = re.findall(SPELLING_PATTERN, words)

    if len(matches) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Supply a sentence containing the word to add surrounding by [square] brackets.")
        return

    print(f"Matches = {matches}")

    # search_matches = ['*' if word in matches else word for word in context.args]
    # result_words = ['*'*(len(word)-2) if word.strip("[]") in matches else word for word in context.args]
    result_words = ['*'*(len(re.sub(ALPHABET_PATTERN, '', word))) if re.sub(ALPHABET_PATTERN, '', word) in matches else word for word in context.args]

    print(f"result_words = {result_words}")

    for w in matches:
        spell_add_word(w, result_words)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Added '{matches}' to the list")

# Handler for when the /clear_spell command is received
async def clear_spell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spell_clear()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Cleared all the spellings")

# Handler for when the /list_spell command is received
async def list_spell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    spellings = spell_load()
    for word in spellings["words"]:
        text += word["word"]
        text += " : "
        text += " ".join(word["sentence"])
        text += "\n"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def spell_clear():
    spellings = {"words": []}
    with open(SPELLING_FILE, 'w') as f:
        f.write(json.dumps(spellings))

def spell_add_word(word, sentence):
    spellings = {}
    with open(SPELLING_FILE, 'r') as f:
        filedata = f.read()
        spellings = json.loads(filedata)

        spellings["words"].append({"word": word, "sentence": sentence})

    with open(SPELLING_FILE, 'w') as f:
        f.write(json.dumps(spellings, indent=2))

def spell_load():
    with open(SPELLING_FILE, 'r') as f:
        filedata = f.read()
        spellings = json.loads(filedata)
        return spellings


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Telegram Bot")
    parser.add_argument('--token', help='Telegram API token', required=True)

    args = parser.parse_args()

    application = ApplicationBuilder().token(args.token).build()
    
    start_handler = CommandHandler('start', start_cmd)
    help_handler = CommandHandler('help', help_cmd)
    add_spell_handler = CommandHandler('add_spell', add_spell_cmd)
    clear_spell_handler = CommandHandler('clear_spell', clear_spell_cmd)
    list_handler = CommandHandler('list_spell', list_spell_cmd)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(add_spell_handler)
    application.add_handler(clear_spell_handler)
    application.add_handler(echo_handler)
    application.add_handler(list_handler)
    application.add_handler(unknown_handler) # MUST BE LAST!

    try:
        with open(SPELLING_FILE, "r") as f:
            data = f.read()
            j = json.loads(data)
            print(f"Words = {j['words']}")
    except:
        spell_clear()
    
    application.run_polling()


