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

