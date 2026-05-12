"""
Detection logic to handle detecting cards from a frame.

Author: Tyler Thompson
"""

import cv2 as cv
import numpy as np

from template_matching import template_matching


def warp_card(frame, corners):
    """
    Takes the corners provided by approxPolyDP and maps them to flatten a card
    :param frame: the raw grayscale input frame
    :param corners: the original 4 corner coordinates of the card
    :return: the flattened card image
    """
    corners = corners.reshape(4, 2).astype(np.float32)
    corner_dest = np.array([[0, 0], [200, 0], [200, 300], [0, 300]], np.float32) # flat card shape coords
    warped = cv.warpPerspective(frame, cv.getPerspectiveTransform(corners, corner_dest), (200, 300))
    return warped

def detection(contours, gray_image):
    """
    Finds each individual detected card, passes it through template_matching, and returns the detected cards
    :param contours: the outer edges of shapes produced by Canny
    :param gray_image: the raw grayscale input frame
    :return: a tuple of the detected cards (KH, AS, etc) and the corners of each card to draw contours on the output
    frame
    """
    cards = []
    for contour in contours:
        # Ramer algorithm to simplify contour to corners, if there are 4 corners, it is likely a card, add area
        # threshold to remove smaller rectangles
        approx = cv.approxPolyDP(contour, 0.03 * cv.arcLength(contour, True), True)
        if len(approx) == 4:
            area = cv.contourArea(contour)
            if area > 400:
                cards.append(approx)

    gray_resized = np.array(gray_image)
    warped_cards = []
    for card_corners in cards:
        warped = warp_card(gray_resized, card_corners)
        warped_cards.append(warped)

    cards_found = template_matching(warped_cards)

    return cards_found, cards