# Image-Processing-Blackjack-Card-Counting-Project
## Overview
Blackjack card counter utilizing Canny edge detection, contour finding, polygonal approximation, normalized cross correlation template matching, and the Hi-Lo card counting algorithm to track the count over Blackjack hands, giving the player a slight edge over the house.

##Example Detection
<img width="800" height="450" alt="detection-ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/148907de-b232-4a3e-a3b4-29f65f3cdbca" />

## Demo Video
A few simulation hands showing the shifting counts, card detections, and changing bet sizes!
https://youtu.be/FyH2guCCPNs

## Pipeline
*Canny Edge Detection
  *Gaussian Blur
  *Gradient Computation
  *Non-Maximum Suppression
  *Hysteresis Thresholding
*Contour Detection
*Perspective Transform
*Template Matching (NCC)
*Hi-Lo Counting

## Setup
Running main with an external webcam will execute the program. While template files are attached, please capture your own templates. Lighting, varying decks, and angles are expected to be consistent from the templates to the live hands. To capture your own templates, run main and position the card you would like to get a template for in frame. Press 's' once a card is detected and enter the number of the card (or the first letter if it is a face card), followed by the first letter of its suit. For example, the King of Hearts should be named KH. After gathering templates, everything is set up to run! 

## Limitations
*Cards cannot overlap and must be distinguishable from one another
*Currently, only single-deck shoes are supported, as cards are stored in a set
*Template matching requires similar conditions to when the templates were gathered
  *If conditions are similar, template matching is incredibly consistent
  *Even a large enough shift in angle can significantly disrupt template matching

## Theory
If you are interested in each method of the pipeline and the math, feel free to go through this high-level overview!
[theoryblackjack.pdf](https://github.com/user-attachments/files/27659530/theoryblackjack.pdf)

## Author
Tyler Thompson, Davidson College, CSC 364
