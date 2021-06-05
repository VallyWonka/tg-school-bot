import re
from collections import Counter


SPELLCHECK_TUTORIAL = """Чтобы проверить своё предложение на ошибки, используй команду /spellcheck \
и через пробел напиши своё предложение.

Пример команды:
/spellcheck Я люлбю боклажан.

Исправленные слова, а также те, которые я не смог исправить, но в них, скорее всего, есть ошибка, \
будут выделены <b>жирным</b>."""


def get_counts(text):
    t = re.split('\W+', text)
    count_dict = Counter(t)
    return count_dict


def get_edits(in_word):
    out_word_list = []
    alphabet = 'абвгдежзийклмнуфхчцшщъыьэюя'
    # missing letter
    for i in range(len(in_word)):
      if i == 0:
        out_word_list.append(in_word[i+1:])
      elif i > 0:
        out_word_list.append(in_word[:i]+in_word[i+1:])
      elif i == len(in_word):
        out_word_list.append(in_word[:-1:])
    
    # neighbor letters are swapped
    for i in range(len(in_word)-1):
      letter1 = in_word[i:i+1]
      letter2 = in_word[i+1:i+2]
      if i == 0:
        out_word_list.append(letter2+letter1+in_word[i+2:])
      elif i > 0:
        out_word_list.append(in_word[:i]+letter2+letter1+in_word[i+2:])
    
    # wrong letter 
    for i in range(len(in_word)-1):
      for c in alphabet:
          out_word_list.append(re.sub(in_word[i], c, in_word, 1))
    
    # extra letter
    for i in range(len(in_word)):
      for c in alphabet:
        if i == 0:
          out_word_list.append(c+in_word[i:])
        elif i > 0:
          out_word_list.append(in_word[:i]+c+in_word[i:])

    return out_word_list


def get_most_likely(in_word, count_dict):
        flag = True
        if in_word in count_dict.keys():
          return in_word, flag
        elif in_word not in count_dict.keys():
          flag = False
          transform_list = get_edits(in_word)
          trans_quantity = 0
          most_likely_word = in_word
          for word in transform_list:
            if word in count_dict.keys():
              if count_dict[word] > trans_quantity:
                trans_quantity = count_dict[word]
                most_likely_word = word
          return most_likely_word, flag

# TODO: editor distance is currently only 1, improve
# TODO: improve output in terms of spaces between words and punctuation
