import random

import sumy
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.kl import KLSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

import nltk

SUMMARIZATION_TUTORIAL = """С помощью функции /summary ты можешь получить файл в формате .txt с сокращённым \
текстом произведения с сайта litra.ru или статьи из Википедии.

Чтобы всё получилось, после команды /summary через нижнее подчёркивание выбери метод сокращения, \
а через пробел вставь ссылку на любую страницу текста нужного тебе произведения или напиши свой запрос в Википедию. 

Какие методы поддерживаются и как их нужно называть?
Luhn - алгоритм Луна;
Lsa - латентно-семантический анализ;
TR - TextRank;
LR - LexRank;
KL - KL-Sum.
Подробнее обо всех этих методах ты можешь узнать \
<a href="https://github.com/miso-belica/sumy/blob/master/docs/summarizators.md">здесь</a>. Если не хочешь выбирать, \
то не надо! Просто не указывай метод, я выберу его за тебя :) О том, какой алгоритм я использовал, \
ты сможешь узнать из названия файла.

Примеры команд:
/summary_Luhn http://www.litra.ru/fullwork/get/woid/00796681240218949757/ = сократить текст с помощью алгоритма Луна;
/summary_Lsa http://www.litra.ru/fullwork/get/woid/00838951240144958312/page/2/ = сократить текст \
с помощью латентно-семантического анализа;
/summary http://www.litra.ru/fullwork/get/woid/00125121284993888894/page/7/ = сократить текст случайным методом;
/summary картошка = найти в Википедии статью по запросу "картошка" и получить её сокращённую версию случайным методом.

Обрати внимание, что для сокращения произведений с сайта litra.ru нужна именно ссылка. Я пока не могу искать \
произведения по названию, но когда-нибудь у меня точно получится!

Также важно, что выполнение этой команды может занять довольно много времени. \
Если на сокращение уйдёт больше 90 секунд, я сообщу тебе об этом и предложу выбрать другой текст или другой метод. \
<b>Подсказка:</b> самый трудоёмкий метод - KL-Sum, именно он обычно работает дольше остальных :)."""

INCORRECT_SUMMARY_COMMAND_MESSAGE = """Чтобы получить сокращённый текст произведения с сайта litra.ru, \
используй команду /summary и через пробел вставь ссылку на него.
Пример команды:
/summary http://www.litra.ru/fullwork/get/woid/00796681240218949757/

Чтобы узнать больше об этой функции, используй команду /summary_tutorial."""

ALGORITHMS = {"luhn": LuhnSummarizer,
              "lsa": LsaSummarizer,
              "tr": TextRankSummarizer,
              "lr": LexRankSummarizer,
              "kl": KLSummarizer}


def summarization(text: str, n_sents: int, language="russian", algorithm=None):
    parser = PlaintextParser.from_string(text, Tokenizer(language))
    stemmer = Stemmer(language)
    if not algorithm or algorithm not in ALGORITHMS:
        algorithm = random.choice(list(ALGORITHMS.items()))[1]
    else:
        algorithm = ALGORITHMS[algorithm]
    summarizer = algorithm(stemmer)
    summarizer.stop_words = nltk.corpus.stopwords.words("russian")
    result = "\n".join(str(sentence) for sentence in summarizer(parser.document, n_sents))
    algorithm = algorithm.__name__.removesuffix("Summarizer")
    return result, algorithm
    # TODO: customisable num_sents
    # TODO: smart num_sents for wiki
    # TODO: use the simplest summarization methods instead of random

