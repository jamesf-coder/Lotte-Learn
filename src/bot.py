
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler
import argparse
import logging
import json
import re
import random

from enum import Enum

HELP = """
Commands:
/start: Starts the quiz.
/stop: Stop the quiz.
/add_spell: Adding a new spelling, like so:
    '/add_spell An [example] spelling'
/list_spell: List all the spellings
/clear_spell: Clear all the spellings
"""

SPELLING_FILE = "spellings.json"
SPELLING_PATTERN = r'\[(.*?)\]'
ALPHABET_PATTERN = r'[^a-zA-Z\s]+'

# Use @RawDataBot http://t.me/RawDataBot to get the IDs of Stickers
# You want to use the file_id
WELLDONE_STICKERS = [
    "CAACAgIAAxkBAAEmu-NlJThppM8y4xFYJdA27V5J5PUbfwACpwADFkJrCtlzNEqUNHMpMAQ",
    "CAACAgIAAxkBAAEmu_FlJTkT5jFLDRALKg9irUYGPY_TUAACMwcAAkb7rAQfTxF2ZTAiJzAE",
    "CAACAgIAAxkBAAEmu_NlJTktf4tvhZzfbeyiKluSOcq4kQACLgEAAvcCyA89lj6kwiWnGjAE",
    "CAACAgIAAxkBAAEmu_dlJTlFes39cMa_G2mAEStL3uvRcQACoAADwZxgDFeN0A5Zq2liMAQ",
    "CAACAgIAAxkBAAEmu_1lJTmFAQjf3neNaCIWem6qhys0-wACgAADwZxgDDUiPX15tvOeMAQ",
    "CAACAgIAAxkBAAEmu_9lJTma1jn8XbuVqXZQoftrN7GWvAACbQADDbbSGXrQ_P4JcJtVMAQ",
    "CAACAgIAAxkBAAEmvANlJTmpGFUOm46AjPTFOKJUTba9iQACZgADWbv8JZy8mJK_t4cXMAQ",
    "CAACAgIAAxkBAAEmvAVlJTm3MHb-CfdS3qubRNF8E2N0TAACagADwDZPE_6bl3vsHAfaMAQ",
    "CAACAgIAAxkBAAEmvAdlJTnH1XlW5ta9aDLPVL_JSiAG9gACZQADmL-ADY4txY9SwuLhMAQ",
    "CAACAgIAAxkBAAEmvAtlJTnczbLIn91TCL61SK2l291ViwACTgADrWW8FCFszl8rK9s8MAQ", 
    "CAACAgIAAxkBAAEmvA1lJTn5Gj9v1K9ykZfpyF_emh9uSAACGwADJHFiGn2Usm5BdDAcMAQ", 
    "CAACAgIAAxkBAAEmvA9lJToHl0RyY7s7ISTjRUHa9q5HawACGQADspiaDkQHunBK4gPsMAQ"
]

FINISH_ANIMS = [
    "https://giphy.com/gifs/strangerthings-netflix-stranger-things-MViYNpI0wx69zX7j7w"
    #"CgACAgQAAxkBAAEmvBdlJTslPI0oGJlKaVXaYgV-520v-wACNwMAAka2BVOW4YhPu7MVCTAE",
    #"CgACAgQAAxkBAAEmvBllJTtH9YJ54Q8L4mSTtbRM76B90QAC9wIAAudXHVOgzIpVMMXrGzAE"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class State(Enum):
    IDLE = 1
    QUIZ = 2

class LottieLearn:

    state:State = State.IDLE
    score:int = 0

    spellings = []
    spellings_idx = 0

    def __init__(self):
        self.application = ApplicationBuilder().token(args.token).read_timeout(7).get_updates_read_timeout(42).build()
        
        start_handler = CommandHandler('start', self.start_cmd)
        stop_handler = CommandHandler('stop', self.stop_cmd)
        help_handler = CommandHandler('help', self.help_cmd)
        add_spell_handler = CommandHandler('add_spell', self.add_spell_cmd)
        clear_spell_handler = CommandHandler('clear_spell', self.clear_spell_cmd)
        list_handler = CommandHandler('list_spell', self.list_spell_cmd)
        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo)
        unknown_handler = MessageHandler(filters.COMMAND, self.unknown)

        self.application.add_handler(start_handler)
        self.application.add_handler(stop_handler)
        self.application.add_handler(help_handler)
        self.application.add_handler(add_spell_handler)
        self.application.add_handler(clear_spell_handler)
        self.application.add_handler(echo_handler)
        self.application.add_handler(list_handler)
        self.application.add_handler(unknown_handler) # MUST BE LAST!

        # try loading the spellings, if not found then create an empty list
        try:
            with open(SPELLING_FILE, "r") as f:
                data = f.read()
                j = json.loads(data)
                print(f"Words = {j['words']}")
        except:
            self.spell_clear()

        self.spellings = self.spell_load()["words"]


    def run(self):
        # run forver
        self.application.run_polling()

    # Handler for when the /start command is received
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.state = State.QUIZ
        self.spellings_idx = 0
        await context.bot.send_dice(chat_id=update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="MarkdownV2", text="__*Starting the quiz*__")
        await self.spell_question(update, context)

    # Handler for when the /stop command is received or we have finished the quiz
    async def stop_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.state = State.IDLE

        qcount = len(self.spellings)

        print(random.sample(FINISH_ANIMS, k=1)[0])
        await context.bot.send_animation(chat_id=update.effective_chat.id, animation=random.sample(FINISH_ANIMS, k=1)[0])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Stopping the quiz.  Score = {self.score}/{qcount}")

    # Handler for when the /help command is received
    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=HELP)

    # Handler for when the /add_spell command is received
    async def add_spell_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        # construct a list from the provided words, replacing any words surrounded by square brackets with ***
        # E.g. ["This", "is", "an", "[example]"] -> ["This", "is", "an", "*******"]
        result_words = ['*'*(len(re.sub(ALPHABET_PATTERN, '', word))) if re.sub(ALPHABET_PATTERN, '', word) in matches else word for word in context.args]

        print(f"result_words = {result_words}")

        for w in matches:
            self.spell_add_word(w, result_words)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Added '{matches}' to the list")

    # Handler for when the /clear_spell command is received
    async def clear_spell_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.spell_clear()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Cleared all the spellings")

    # Handler for when the /list_spell command is received
    async def list_spell_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "<u>Spellings</u>\n"
        for word in self.spellings:
            text += "<b>" + word["word"] + " : </b>"
            text += " ".join(word["sentence"])
            text += "\n"

        await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="HTML", text=text)

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.state == State.QUIZ:

            if self.spellings_idx >= len(self.spellings):
                await self.stop_cmd(update, context)
                return

            # check the input to see if it matches the quiz question
            print(f"test = {update.message.text}")
            if update.message.text.strip().lower() == self.spellings[self.spellings_idx]["word"].lower():
                self.score += 1
                await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=random.sample(WELLDONE_STICKERS, k=1)[0])
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Welldone!")
                self.spellings_idx += 1
                await self.spell_question(update, context)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong, try again.")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Start a quiz by entering: '/start'")

    # the unknown callback
    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

    async def spell_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.spellings_idx >= len(self.spellings):
            await self.stop_cmd(update, context)
            return
        
        q = " ".join(self.spellings[self.spellings_idx]['sentence'])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Q: {q}")

    # clear all the spellings
    def spell_clear(self):
        self.spellings = []
        with open(SPELLING_FILE, 'w') as f:
            f.write(json.dumps({"words": self.spellings}))

    # add a new word in the format, example:
    #   word: "Because"
    #   sentence: ["*******", "it", "is", "hard", "to", "spell"]
    def spell_add_word(self, word: str, sentence: list[str]):
        self.spellings.append({"word": word, "sentence": sentence})

        with open(SPELLING_FILE, 'w') as f:
            f.write(json.dumps({"words": self.spellings}, indent=2))

    # load and return the spellings dictionary
    def spell_load(self):
        with open(SPELLING_FILE, 'r') as f:
            filedata = f.read()
            return json.loads(filedata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Telegram Bot")
    parser.add_argument('--token', help='Telegram API token', required=True)

    args = parser.parse_args()

    logging.warning(f"Token = {args.token}")

    ll = LottieLearn()
    ll.run()



