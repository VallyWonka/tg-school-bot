#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
"""The bot that will make your life easier."""

import re
import logging
import tempfile
from string import punctuation

from func_timeout import func_timeout, FunctionTimedOut
from natasha import Doc, Segmenter, NewsMorphTagger, NewsEmbedding
from wiktionaryparser import WiktionaryParser

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler
from telegram.constants import MAX_CAPTION_LENGTH, MAX_MESSAGE_LENGTH

from setup import PROXY, TOKEN
from sentence_analysis import (
    SENTENCE_TUTORIAL,
    INCORRECT_SYNT_COMMAND_MESSAGE,

    lemmatize,
    morph_analyze,
    synt_analyze
)
from scraper import (
    LITRA_TUTORIAL,
    INCORRECT_LITRA_COMMAND_MESSAGE,
    WIKIPEDIA_TUTORIAL,
    INCORRECT_WIKIPEDIA_QUERY,

    get_litra,
    get_shortwork_link,
    get_wikipedia
)
from check_dic import SPELLCHECK_TUTORIAL, get_most_likely, get_counts
from summarization import SUMMARIZATION_TUTORIAL, INCORRECT_SUMMARY_COMMAND_MESSAGE, summarization

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Natasha instances
SEGMENTER = Segmenter()
EMB = NewsEmbedding()
MORPH_TAGGER = NewsMorphTagger(EMB)

# Litra-button interaction
LITRA_LINK = ""

# Relationship types dictionary
REL_TYPES = {"synonyms": "Синонимы",
             "antonyms": "Антонимы",
             "related terms": "Похожие слова"}


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(f"""Привет, {update.effective_user.first_name}!
Чтобы узнать больше о моих функциях, используй команду /help.""")


def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text("""Вот, что я умею:
/start - сказать "привет" :)
/help - помощь
/suggestion <твоё предложение> - здесь можно оставить фидбек или предложить новую фичу :)

/relwords <слово> - получить синонимы, антонимы и похожие слова к заданному слову

/spellcheck <предложение> - проверить предложение на ошибки
/spellcheck_tutorial - как пользоваться функцией /spellcheck

/sentence(_<виды разбора>) <предложение> - лемматизация, морфологический и синтаксический разбор предложения
/sentence_tutorial - как пользоваться функцией /sentence

/litra <ссылка> - получить текстовый файл с полным текстом произведения с сайта litra.ru
/litra_tutorial - как пользоваться функцией /litra

/summary(_<метод>) <ссылка> - получить сокращённую версию произведения с сайта litra.ru
/summary_tutorial - как пользоваться функцией /summary

/wikipedia <запрос> - получить статью из википедии по запросу
/wikipedia_tutorial - как пользоваться функцией /wikipedia""")


def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f"Update {update} caused error {context.error}")


def sent_tutorial(update: Update, context: CallbackContext):
    """Explain the sentence function."""
    update.message.reply_text(SENTENCE_TUTORIAL)


def suggestion(update: Update, context: CallbackContext):
    with open("suggestions.txt", "a", encoding="utf-8") as file:
        file.write(f"{update.effective_user['username']}\t{update.message.text.removeprefix('/suggestion ')}\n")
    update.message.reply_text("Спасибо, что помогаешь мне стать лучше!")
    # TODO: create a database with reviews and suggestions


def sent_analyze(update: Update,
                 context: CallbackContext,
                 lemmatization=True,
                 morph_analysis=True,
                 synt_analysis=True):
    """Analyze the user sentence."""
    # Get parameters
    commands = re.match(r"/sentence_([A-Z]{,3})", update.message.text)
    if commands:
        processed_commands = [item in commands.group(1) for item in "LMS"]
        if any(processed_commands):
            lemmatization, morph_analysis, synt_analysis = processed_commands
        else:
            update.message.reply_text(INCORRECT_SYNT_COMMAND_MESSAGE)
            return

    # Get sentence
    sent = " ".join(update.message.text.split()[1:])
    if len(sent) == 0:
        update.message.reply_text(INCORRECT_SYNT_COMMAND_MESSAGE)
        return

    message_lemmas, message_morph, message_synt, synt_tree = None, None, None, None

    # Prerocess the sentence
    doc = Doc(sent)
    doc.segment(SEGMENTER)

    # Lemmatize
    if lemmatization:
        message_lemmas = lemmatize(doc)

    # Morph tagging
    if morph_analysis:
        message_morph = morph_analyze(doc)

    # Syntax parsing
    if synt_analysis:
        message_synt, synt_tree = synt_analyze(doc)

    # Send results
    message_text = "\n\n".join([message for message in [message_lemmas, message_morph, message_synt] if message])

    if synt_analysis and synt_tree:
        if len(message_text) <= MAX_CAPTION_LENGTH:
            update.message.reply_photo(synt_tree, caption=message_text)
            return
        else:
            update.message.reply_photo(synt_tree)

    if len(message_text) <= MAX_MESSAGE_LENGTH:
        update.message.reply_text(message_text)
    else:
        filename = re.sub(r"[<>:\"/\\|?*]", "", f"{sent}.txt")
        with tempfile.TemporaryFile(mode="a+", encoding="utf-8") as file:
            file.write(message_text)
            file.seek(0)
            update.message.reply_document(document=file, filename=filename)


def litra_tutorial(update: Update, context: CallbackContext):
    """Explain the litra function."""
    update.message.reply_text(LITRA_TUTORIAL, disable_web_page_preview=True)


def get_text_litra(update: Update, context: CallbackContext):
    """Get text from litra.ru."""
    global LITRA_LINK
    LITRA_LINK = context.args[0]
    try:
        author, title, full_text = get_litra(LITRA_LINK)[:3]
    except Exception:
        update.message.reply_text(INCORRECT_LITRA_COMMAND_MESSAGE, disable_web_page_preview=True)
        return
    filename = re.sub(r"[<>:\"/\\|?*]", "", f"{author} {title}.txt")
    with tempfile.TemporaryFile(mode="a+", encoding="utf-8") as file:
        file.write(full_text)
        file.seek(0)
        update.message.reply_document(document=file, filename=filename)


def wikipedia_tutorial(update: Update, context: CallbackContext):
    update.message.reply_text(WIKIPEDIA_TUTORIAL)


def get_text_wikipedia(update: Update, context: CallbackContext):
    try:
        title, content, random = get_wikipedia(context.args)
    except Exception as e:
        print(e)
        update.message.reply_text(INCORRECT_WIKIPEDIA_QUERY)
        return

    if random:
        caption = "По твоему запросу ничего не нашлось или он был пуст. Держи случайную страницу!"
    else:
        caption = None

    with tempfile.TemporaryFile(mode="a+", encoding="utf-8") as file:
        file.write(content)
        file.seek(0)
        update.message.reply_document(document=file, filename=f"{title}.txt", caption=caption)


def summary_tutorial(update: Update, context: CallbackContext):
    """Explain the summarize function."""
    update.message.reply_text(SUMMARIZATION_TUTORIAL, parse_mode="HTML", disable_web_page_preview=True)


def summary(update: Update, context: CallbackContext):
    """Summarize user text."""
    litra = False
    random = False
    # Get algorithm parameter
    algorithm = re.search(r"/summary_?([a-zA-Z]{,4})", update.message.text)
    try:
        algorithm = algorithm.group(1).lower()
    except TypeError:
        algorithm = None

    # Warn that it may take a while :)
    update.message.reply_text("Подожди немного...")

    # Get text and info
    if "litra.ru" in update.message.text:
        litra = True
        global LITRA_LINK
        LITRA_LINK = " ".join(update.message.text.split()[1:])
        try:
            author, title, text, num_pages = get_litra(LITRA_LINK)
        except Exception:
            update.message.reply_text(INCORRECT_SUMMARY_COMMAND_MESSAGE, disable_web_page_preview=True)
            return
    else:
        author = "Wikipedia"
        num_pages = 1
        query = update.message.text.split()[1:]
        title, text, random = get_wikipedia(query)
        text = re.sub(r"={2,}.+={2,}", "\n", text)

    # Try summarizing else suggest options
    try:
        summary, algorithm = func_timeout(90, summarization, args=(text, num_pages * 3, "russian", algorithm))
    except FunctionTimedOut:
        if litra:
            keyboard = [[InlineKeyboardButton("Да, поищи сокращённую версию", callback_data="True"),
                         InlineKeyboardButton("Нет, спасибо", callback_data="False")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("""Извини, у меня не получилось справиться с этим текстом! Могу предложить \
поискать уже готовую сокращённую версию текста на litra.ru. Что скажешь?""", reply_markup=reply_markup)
        else:
            update.message.reply_text(f"""Извини, у меня не получилось справиться со статьёй {title}! Попробуй \
использовать другой алгоритм или другой текст.""")
        return

    # Create caption for random articles
    if random:
        caption = "По твоему запросу ничего не нашлось или он был пуст. Держи случайную страницу!"
    else:
        caption = None

    # Create a txt file with summary and send results
    with tempfile.TemporaryFile(mode="a+", encoding="utf-8") as file:
        file.write(summary)
        file.seek(0)
        update.message.reply_document(document=file, filename=f"{algorithm} {author} {title}.txt", caption=caption)
    # TODO: process user file
    # TODO: shorten and simplify this function


def relwords(update: Update, context: CallbackContext):
    """Give synonyms for the user word."""
    word = update.message.text.removeprefix("/relwords ")
    parser = WiktionaryParser()
    parser.set_default_language("russian")
    try:
        related_words = parser.fetch(word)[0]["definitions"][0]["relatedWords"]
    except IndexError:
        update.message.reply_text("""Кажется, ничего не нашлось. Попробуй ещё раз!""")
        return
    message_text = ""
    for reltypes in related_words:
        words = []
        for word in reltypes["words"]:
            no_english = re.sub(r"\s\(.+?\)", "", word)
            if no_english:
                words.append(no_english)
        words = ", ".join(words)
        message_text += f"""{REL_TYPES[reltypes["relationshipType"]]}:\n{words}\n\n"""
    update.message.reply_text(message_text)
    # TODO: not create an instance of parser every time


def spellcheck_tutorial(update: Update, context: CallbackContext):
    """Explain the spellcheck function."""
    update.message.reply_text(SPELLCHECK_TUTORIAL, parse_mode="HTML")


def spellchecker(update: Update, context: CallbackContext):
    """Checks spelling in the given sentence."""
    sent = update.message.text.removeprefix("/spellcheck ")
    if sent == update.message.text:
        update.message.reply_text("""Не забудь вписать предложение для проверки!""")
        return
    new_sent = ""
    doc = Doc(sent)
    doc.segment(SEGMENTER)
    doc.tag_morph(MORPH_TAGGER)
    tokens = [token.text for token in doc.tokens]

    vocab = open("lifenews2.txt", encoding="utf-8").read()
    counts_vocab = get_counts(vocab)
    # TODO: don't load vocab every time

    for word in tokens:
        right_word, flag = get_most_likely(word, counts_vocab)
        if not flag:
            right_word = "*" + right_word + "*"
        if word in punctuation:
            new_sent += word
        right_word += " "
        new_sent += right_word

    update.message.reply_text(f"Проверенное предложение: {new_sent}\n", parse_mode="Markdown")


def button_shortwork(update: Update, context: CallbackContext):
    query = update.callback_query
    global LITRA_LINK
    if query.data == "True":
        try:
            author, title, text = get_litra(get_shortwork_link(LITRA_LINK))[:3]
        except Exception:
            no_shortwork_message = """Кажется, к этому произведению нет \
краткого содержания! Попробуй скачать полный текст с помощью функции /litra."""
            context.bot.send_message(chat_id=str(update.effective_chat['id']), text=no_shortwork_message)
            return
    else:
        another_suggestion = """Ок! Ещё можно попробовать использовать \
другой алгоритм. Чтобы узнать, какие есть, используй функцию /summary_tutorial :)."""
        context.bot.send_message(chat_id=str(update.effective_chat['id']), text=another_suggestion)
        return

    with tempfile.TemporaryFile(mode="a+", encoding="utf-8") as file:
        file.write(text)
        file.seek(0)
        context.bot.send_document(chat_id=str(update.effective_chat['id']), document=file, filename=f"{author} {title}.txt")
    # TODO: don't use global litra link because users might get someone else's queries


def main():
    """Where the magic happens"""

    # Connect via socks proxy
    request_kwargs = {
        "proxy_url": PROXY
    }

    updater = Updater(TOKEN, request_kwargs=request_kwargs, use_context=True)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", chat_help))
    updater.dispatcher.add_handler(CommandHandler("suggestion", suggestion))
    updater.dispatcher.add_handler(CommandHandler("sentence_tutorial", sent_tutorial))
    updater.dispatcher.add_handler(MessageHandler(Filters.regex(r"(/sentence_?[A-Z]{,3})"),
                                                  sent_analyze))
    updater.dispatcher.add_handler(CommandHandler("litra_tutorial", litra_tutorial))
    updater.dispatcher.add_handler(CommandHandler("litra", get_text_litra))
    updater.dispatcher.add_handler(CommandHandler("summary_tutorial", summary_tutorial))
    updater.dispatcher.add_handler(MessageHandler(Filters.regex(r"(/summary_?[a-zA-Z]{,4})"), summary))
    updater.dispatcher.add_handler(CommandHandler("wikipedia_tutorial", wikipedia_tutorial))
    updater.dispatcher.add_handler(CommandHandler("wikipedia", get_text_wikipedia))
    updater.dispatcher.add_handler(CommandHandler("relwords", relwords))
    updater.dispatcher.add_handler(CommandHandler("spellcheck_tutorial", spellcheck_tutorial))
    updater.dispatcher.add_handler(CommandHandler("spellcheck", spellchecker))

    updater.dispatcher.add_handler(CallbackQueryHandler(button_shortwork, pattern='(True|False)'))

    # on noncommand i.e message - echo the message on Telegram
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    logger.info("Start Bot")
    main()


# TODO: unify error messages
# TODO: add logging using databases
# TODO: not use BaseExceptions but understand what is going wrong and why
# TODO: improve code readability, modulate
# TODO: handle pylint warnings
# TODO: process multiple users
# TODO: make user be able to stop the bot
# TODO: add some fun apis
# TODO: customizable environment (e.g. custom timeout in summarization)
# TODO: types annotations (Union и Optional, look for info in saved tg messages)
# TODO: add documentation
