import re


def syllables(word):
    syllables = []
    vowels = set('аяоёыиэеую')
    alphabet = set('абвгдеёзжийклмнопрстуфхцчшщыэюя')
    consonants = alphabet - vowels
    counter = 0
    for i in range(len(word)):
        if word[i] in vowels:
            syllables.append(word[counter:i + 1])
            counter = i + 1
        elif word[i] in 'ъь':
            syllables[-1] += word[i - 1] + word[i]
            counter = i + 1
        elif i > 1 and i < len(word) - 1 and word[i] in consonants and word[i + 1] in consonants:
            syllables[-1] += word[i]
            counter = i + 1
        elif i == len(word) - 1 and word[i] in consonants:
            syllables[-1] += word[i]
        print(syllables)
    syllables[len(syllables) // 2 - 1] += '.'
    return ''.join(syllables[0:len(syllables) // 2])


def shorten(word):
    conventional = {"теория": "теор.", "практикум": "практ.", "прикладная": "прикл.",
                    "математическая": "мат.", "компьютерная": "комп.","теоретическая":"теор.","физическая":"физ."}
    vowels = set('аяоёыиэеую')
    alphabet = set('абвгдеёзжийклмнопрстуфхцчшщыэюя')
    consonants = alphabet - vowels
    m = len(word) // 2 - 1
    if word in conventional:
        return conventional[word]
    elif word[m] in consonants and word[m + 1] in 'ъь':
        return ''.join(word[:m + 2]) + '.'
    elif word[m] in consonants:
        return ''.join(word[:m + 1]) + '.'
    elif m == 0:
        return word
    else:
        return ''.join(word[:m]) + '.'
