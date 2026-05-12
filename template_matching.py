"""
Applies Normalized Cross Correlation to match each detected card to its template with the correct card value

Author: Tyler Thompson
"""

import glob
import numpy as np

from PIL import Image
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

card_cache = {}
cache_misses = 0

def mean(image):
    """
    Calculates the mean of the image
    :param image: image to find mean of
    :return: the mean of the image
    """
    M, N = image.size
    sum = 0
    count = 0
    for v in range(N):
        for u in range(M):
            sum += image.getpixel((u,v))
            count += 1
    return sum / count

def match(card):
    """
    Compares each detected card in paralel to supplied template images to determine its best match.
    :param card: The current card to match
    :return: the name of the card (KH, AS, etc)
    """
    # Logic to first determine suit to template match 4 times less
    # Too inconsistent to use
    #
    # folder = "suits"
    # suit_card = card.crop((175, 45, 200, 70))
    # suit = match_helper(suit_card, folder, .4)
    # print(suit)
    #
    # if suit == "clubs":
    #     folder = "clubs_templates"
    #     return match_helper(card, folder, .65)
    # if suit == "spades":
    #     folder = "spades_templates"
    #     return match_helper(card, folder, .65)
    # if suit == "diamonds":
    #     folder = "diamonds_templates"
    #     return match_helper(card, folder, .65)
    # if suit == "hearts":
    #     folder = "hearts_templates"
    #     return match_helper(card, folder, .65)
    # return None

    global cache_misses
    threshold = .75
    M, N = card.size
    card_mean = mean(card)
    cache_args = []

    # we first check the cache to perform less computations
    if card_cache:
        for cache_template in list(card_cache.keys()):
            if card_cache[cache_template] > 10:
                card_cache.pop(cache_template, None)
            cache_args.append(((M, N), cache_template, card, card_mean, threshold))
        with ThreadPoolExecutor(max_workers=10) as executor:
            correlation = list(executor.map(match_template, cache_args))

        best_match_tuple = max(correlation, key=lambda x: x[1])
        best_match = best_match_tuple[0]

        if best_match_tuple[1] >= threshold:
            card_cache[best_match] = 0
            return best_match.stem.rsplit("_", 1)[0]
        if best_match in card_cache:
            card_cache[best_match] += 1

    # if cache missed
    folder = "templates"
    return match_helper(card, folder, threshold)

# Operations done in Pillow. No numpy
# def match_helper(card, folder, threshold):
#     M, N = card.size
#     card_mean = mean(card)
#
#     score = -1
#     best_match = None
#
#     for template_file in glob.glob(f"{folder}/*"):
#         template = Image.open(template_file).resize((M, N))
#         template_mean = mean(template)
#
#         numerator = 0
#         denominator_1 = 0
#         denominator_2 = 0
#
#         for v in range(N):
#             for u in range(M):
#                 numerator += (card.getpixel((u, v)) - card_mean) * (template.getpixel((u, v)) - template_mean)
#                 denominator_1 += (card.getpixel((u, v)) - card_mean) ** 2
#                 denominator_2 += (template.getpixel((u, v)) - template_mean) ** 2
#         val = numerator / ((denominator_1 * denominator_2) ** .5)
#         if val >= score:
#             score = val
#             best_match = Path(template_file)
#             if score >= threshold:
#                 return best_match.stem
#     return None

def match_helper(card, folder, threshold):
    """
    Helper to match to calculate difference score between templates and detected card
    :param card: The current card to match
    :param folder: the folder that houses the templates
    :param threshold: minimum requirement for the best match to be confirmed as a mnatch
    :return: the name of the card (KH, AS, etc)
    """
    M, N = card.size
    card_mean = mean(card)

    correlation = []
    args = []
    for template_file in glob.glob(f"{folder}/*"):
        args.append(((M, N), template_file, card, card_mean, threshold))

    with ThreadPoolExecutor(max_workers=10) as executor:
        correlation = list(executor.map(match_template, args))

    best_match_tuple = max(correlation, key=lambda x: x[1])
    best_match = best_match_tuple[0]

    if best_match_tuple[1] >= threshold:
        card_cache[best_match] = 0
        return best_match.stem.rsplit("_", 1)[0]

    return None

# def match_template(args):
#     (M, N), template_file, card, card_mean, threshold = args
#     template = Image.open(template_file).resize((M, N))
#     template_mean = mean(template)
#
#     numerator = 0
#     denominator_1 = 0
#     denominator_2 = 0
#
#     for v in range(N):
#         for u in range(M):
#             numerator += (card.getpixel((u, v)) - card_mean) * (template.getpixel((u, v)) - template_mean)
#             denominator_1 += (card.getpixel((u, v)) - card_mean) ** 2
#             denominator_2 += (template.getpixel((u, v)) - template_mean) ** 2
#     val = numerator / ((denominator_1 * denominator_2) ** .5)
#     return Path(template_file), val
#     # if val >= score:
#     #     score = val
#     #     best_match = Path(template_file)
#     #     if score >= threshold:
#     #         return best_match.stem

def match_template(args):
    """
    Helper to allow for parallel computations. Here, each template runs parallel to one another (if enough cores are
    available)
    :param args: iterable element tuple to unpack
    :return: the match score
    """
    (M, N), template_file, card, card_mean, threshold = args

    card_arr = np.array(card, float)
    card_zero = card_arr - card_mean

    template = Image.open(template_file).resize((M, N))
    t_arr = np.array(template, float)
    t_zero = t_arr - t_arr.mean()

    numerator = np.sum(card_zero * t_zero)
    denominator = (np.sum(card_zero ** 2) * np.sum(t_zero ** 2)) ** 0.5

    if denominator == 0:
        return Path(template_file), -1

    val = numerator / denominator
    return Path(template_file), val

def template_matching(cards):
    """
    Matches each detected card to a template image and returns what the card likely is
    :param cards: The detected cards to match
    :return: The set of detected cards
    """
    cards_found = []
    for i in range(len(cards)):
        cards[i] = Image.fromarray(cards[i])

    # match each detected card in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        cards_found = list(executor.map(match, cards))

    return cards_found