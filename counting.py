"""
Implements the Hi-Lo card counting algorith. Cards 2-6 carry a value of +1, 10-A carry a value of -1, and 7-9 are
neutral and carry a value of 0.

Author: Tyler Thompson
"""

def update_count(cards):
    """
    Updates the count
    :param cards: set of found cards
    :return: the running count
    """
    count = 0
    for card in cards:
        count += update_count_helper(card)
    return count

def update_count_helper(card):
    """
    Helper to determine the Hi-Lo value of each detected card
    :param card: the card to determine the value of
    :return: 1 if low, -1 if high, 0 if neutral
    """
    suits = ['S', 'C', 'H', 'D']
    high = ['10', 'J', 'K', 'Q', 'A']

    for num in range(2, 7):
        for suit in suits:
            curr = str(num) + suit
            if card == curr:
                return 1

    for num in high:
        for suit in suits:
            curr = str(num) + suit
            if card == curr:
                return -1

    return 0