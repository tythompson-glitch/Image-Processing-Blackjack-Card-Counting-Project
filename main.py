"""
Blackjack card counter utilizing Canny edge detection, contour finding, polygonal approximation, normalized cross
correlation template matching, and the Hi-Lo card counting algorithm to track the count over Blackjack hands giving
the player a slight edge over the house

main.py inputs frames from a live video to compute operations on to track the count

Author: Tyler Thompson
"""

from canny_edge_detection import gauss_blur, get_Gx, get_Gy, get_edge_strength, non_max_suppression, trace_and_threshold
from counting import update_count
from detection import detection, warp_card

from PIL import Image
import numpy as np
import cv2 as cv
import time
import sys

sys.setrecursionlimit(100000)

def main():
    """
    Inputs frames from a live video to compute operations on to track the count
    """
    cards = []
    t_lo = .04 # lower bound threshold
    t_hi = .08 # upper bound threshold
    cap = cv.VideoCapture(1)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    count = 0
    last_no_cards = 0
    card_set = set()
    units = 0

    cv.namedWindow('frame', cv.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # preprocessing, convert to gray, reduce size, and apply gaussian blur
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray_image = Image.fromarray(gray)
        gray_image = gray_image.resize((640, 360))
        blur_img = gauss_blur(gray_image, 2)

        # gradient computations
        Gx = get_Gx(blur_img)
        Gy = get_Gy(blur_img)
        edge_strength = get_edge_strength(blur_img, Gx, Gy)

        max_mag_map = non_max_suppression(blur_img, edge_strength, Gx, Gy)

        # hysteresis thresholding
        binary_edge_map = trace_and_threshold(max_mag_map, t_lo, t_hi)

        # convert edge map to pillow, scale to 0 and 255, change from float to int
        edges = (np.array(binary_edge_map) * 255).astype(np.uint8)

        #find only outer edges of shapes, discard unnecesary info from second part of tuple
        contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # detection
        cards_found, cards = detection(contours, gray_image)
        if cards_found and len(cards) != last_no_cards:
            card_set.update(cards_found)
            card_set.discard(None)
            count = update_count(card_set)
            last_no_cards = len(cards)

        # units to bet logic
        if count <= 0:
            units = 1
        elif count == 1:
            units = 2
        elif count == 2:
            units = 4
        elif count == 3:
            units = 6
        elif count == 4:
            units = 8
        elif count >= 5:
            units = 10

        cv.resizeWindow('frame', 1280, 720)

        # draw detected card contours on frame for visualization
        display = cv.cvtColor(np.array(blur_img), cv.COLOR_GRAY2BGR)
        cv.drawContours(display, cards, -1, (0, 255, 0), 2)

        # write count and bet size to frame
        cv.putText(display, f"Count: {count}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 0), 2)
        cv.putText(display, f"Bet Size: {units} units", (10, 70), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # to see detected cards, good for testing
        # cv.putText(display, f"Cards: {list(card_set)}", (10, 50), cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 2)
        # print(f"Cards: {list(card_set)}")


        cv.imshow('frame', display)

        key = cv.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('s'): # for saving more templates
            gray_resized = np.array(gray_image)
            for i, card_corners in enumerate(cards):
                warped = warp_card(gray_resized, card_corners)
                card_name = input(f"Enter card: ")
                cv.imwrite(f"templates/{card_name}_{int(time.time())}.png", warped)
                print(f"Saved {card_name}")

    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()