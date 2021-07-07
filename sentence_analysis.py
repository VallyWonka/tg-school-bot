import requests
from ipymarkup import format_dep_markup
from natasha import MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc
from setup import HCTI_API_KEY, HCTI_API_USER_ID

# Natasha instances
EMB = NewsEmbedding()
MORPH_TAGGER = NewsMorphTagger(EMB)
MORPH_VOCAB = MorphVocab()
SYNTAX_PARSER = NewsSyntaxParser(EMB)

# HCTI
HCTI_API_ENDPOINT = "https://hcti.io/v1/image"

POS_TAGS = {"ADJ": "прилагательное", "ADP": "предлог/послелог", "ADV": "наречие", "AUX": "вспом. глагол",
            "CCONJ": "сочинительный союз", "DET": "артикль", "INTJ": "междометие", "NOUN": "существительное",
            "NUM": "числительное", "PART": "частица", "PRON": "местоимение", "PROPN": "имя собственное",
            "PUNCT": "знак пунктуации", "SCONJ": "подчинительный союз", "SYM": "символ", "VERB": "глагол",
            "X": "другое/неизвестно"}

FEATS_TAGS = {"Animacy": {"Anim": "одуш.", "Inan": "неодуш."},
              "Aspect": {"Perf": "сов. вид", "Imp": "несов. вид"},
              "Case": {"Acc": "вин. п.", "Dat": "дат. п.", "Gen": "род. п.", "Ins": "тв. п.", "Nom": "им. п.",
                       "Loc": "предл. п. (в знач. локатива)", "Par": "род. п. (в знач. партитива)",
                       "Voc": "звательная форма"},
              "Degree": {"Cmp": "сравнит. степ.", "Pos": "нейтр. степ.", "Sup": "превосх. степ."},
              "Gender": {"Fem": "жен. род", "Masc": "муж. род", "Neut": "ср. род"},
              "Mood": {"Cnd": "усл. накл.", "Ind": "изъявит. накл.", "Imp": "повелит. накл."},
              "NumType": {"Card": "колич."},
              "Number": {"Plur": "множ. ч.", "Sing": "ед. ч."},
              "Person": {"1": "1 л.", "2": "2 л.", "3": "3 л."},
              "Polarity": {"Neg": "отрицание"},
              "Tense": {"Fut": "буд. вр.", "Past": "прош. вр.", "Pres": "наст. вр."},
              "Variant": {"Short": "кратк."},
              "VerbForm": {"Conv": "дееприч.", "Fin": "личн. форма", "Inf": "инфинитив (нач. форма)", "Part": "прич."},
              "Voice": {"Act": "акт. залог", "Mid": "средн. залог", "Pass": "пасс. залог"},
              "Abbr": {"Yes": "аббревиатура"},
              "Foreign": {"Yes": "иноязычное слово"},
              "Reflex": {"Yes": "возвратн."},
              "Typo": {"Yes": "опечатка"},
              "NumForm": {"Digit": "арабская запись числа"}}


def lemmatize(doc: Doc):
    doc.tag_morph(MORPH_TAGGER)
    for token in doc.tokens:
        token.lemmatize(MORPH_VOCAB)
    lemmas = [f"{id + 1}) {token.text} → {token.lemma}" for id, token in enumerate(doc.tokens) if
              not token.pos == "PUNCT"]
    message = "Токены и леммы:\n{}".format("\n".join(lemmas))
    return message


def morph_analyze(doc: Doc):
    doc.tag_morph(MORPH_TAGGER)
    morph_tags = []
    for ind, token in enumerate(doc.tokens):
        if not token.pos == "PUNCT":
            features = [FEATS_TAGS[feat][tag] for feat, tag in token.feats.items()]
            morph_tags.append(f"{ind + 1}) {token.text}: {POS_TAGS[token.pos]}, {', '.join(features)}")
    message = "Морфологический разбор:\n{}".format("\n".join(morph_tags))
    return message


def synt_analyze(doc: Doc):
    # Tokenize
    tokens = [token.text for token in doc.tokens]

    # Analyze
    doc.parse_syntax(SYNTAX_PARSER)
    synt_spans, synt_tags = [], []
    for ind, token in enumerate(doc.tokens):
        head_id = int(token.head_id.split("_")[1]) - 1
        relation = token.rel
        if head_id == ind:
            synt_spans.append((-1, ind, "root"))
            relation = "root"
        else:
            synt_spans.append((head_id, ind, relation))
        if relation != "root":
            synt_tags.append(f"{ind + 1}) {token.text} ←{relation}— {tokens[head_id]}")
        else:
            synt_tags.append(f"{ind + 1}) {token.text} — {relation}")

    # Send results
    message = "Синтаксический разбор:\n{}".format("\n".join(synt_tags))

    # Draw the syntax tree
    try:
        data = {"html": "\n".join(list(format_dep_markup(tokens, synt_spans)))}
    except ValueError:
        return message, None

    image = requests.post(url=HCTI_API_ENDPOINT, data=data, auth=(HCTI_API_USER_ID, HCTI_API_KEY))
    image_url = image.json()['url']
    return message, image_url
    # TODO: translate tags
    # TODO: find another service so that there is no query limit
    # TODO: object oriented version
    # TODO: school mode and scientist mode
