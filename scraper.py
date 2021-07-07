import re
import random as rnd

import requests
import wikipedia
from wikipedia.exceptions import PageError, DisambiguationError
from bs4 import BeautifulSoup

wikipedia.set_lang("ru")


def get_litra(url: str):
    given_page = requests.get(url)
    html_soup = BeautifulSoup(given_page.text, 'lxml')

    num_pages = re.search(r"\[\d+/(\d+)\]", html_soup.find("h1").get_text())
    if num_pages:
        num_pages = int(num_pages.group(1))
    else:
        num_pages = 1

    author = html_soup.find("h2").get_text().split(" /  ")[1]

    download_link = "http://www.litra.ru" \
                    + html_soup.find("a",
                                     text=re.compile(r"Скачать полное произведение|Скачать краткое содержание|Скачать "
                                                     r"сочинение"))["href"]

    full_text_page = requests.get(download_link)
    html_soup = BeautifulSoup(full_text_page.text, 'lxml')
    title = html_soup.find("h1").get_text()
    html_soup.h1.decompose()
    for _ in html_soup.find_all("a"):
        html_soup.a.decompose()
    copyright_old = """2008 
Created by Litra.RU Team / 
"""
    copyright_new = """
Created by Litra.RU Team
"""
    full_text = re.sub(r"\n{2,}", "\n", html_soup.find("body").get_text(separator="\n")).replace(copyright_old,
                                                                                                 copyright_new)

    return author, title, full_text, num_pages


# TODO: search by title, not only by link


def wikisource(query: str):
    pass


# TODO: get texts from wikisource


def get_shortwork_link(url: str):
    given_page = requests.get(url)
    html_soup = BeautifulSoup(given_page.text, 'lxml')
    shortwork_link = "http://www.litra.ru" \
                     + html_soup.find("a",
                                      text=re.compile(r"Краткое содержание"))["href"]
    return shortwork_link


def disambiguation_error(query: str):
    page = requests.get(f"https://ru.wikipedia.org/wiki/{query}")
    html_soup = BeautifulSoup(page.text, 'lxml')
    main_body = html_soup.find("div", class_="mw-parser-output")
    options = main_body.find_all("li", class_=None)
    possible_headers = []
    for option in options:
        try:
            title = option.a.attrs["title"]
        except (AttributeError, KeyError):
            continue
        if all(item not in title for item in ["(страница отсутствует)", "(значения)"]):
            possible_headers.append(title)
    return possible_headers


def get_wikipedia(query: list, random=False):
    if len(query) == 0:
        query = [wikipedia.random()]
        random = True
    elif "ru.wikipedia.org" in query[0]:
        page = requests.get(query[0])
        query = [BeautifulSoup(page.text, 'lxml').find("h1").get_text()]
    query = " ".join(query)
    try:
        page = wikipedia.page(query, auto_suggest=False)
    except PageError:
        try:
            page = wikipedia.page(query)
        except PageError:
            return get_wikipedia([wikipedia.random()], random=True)
        except DisambiguationError as error:
            query = rnd.choice(disambiguation_error(error.title))
            page = wikipedia.page(query, auto_suggest=False)
    except DisambiguationError:
        query = rnd.choice(disambiguation_error(query))
        page = wikipedia.page(query, auto_suggest=False)
    title = page.title
    content = page.content
    return title, content, random


# TODO: include media? return as pdf? at least format the result better
# TODO: the function seems too crowded, reformat, simplify, or redo
# TODO: when loading pages from wiki, don't resolve disambiguation randomly but suggest options via buttons
# TODO: when loading texts from wiki, disambiguation might be on multiple levels (ход - чёрный ход),
#  come up with a solution for that

