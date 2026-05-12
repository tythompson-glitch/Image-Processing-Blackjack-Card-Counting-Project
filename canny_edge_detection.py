"""
Canny edge detection methods. Each step to produce the edge image is done here.

Author: Tyler Thompson
"""

from PIL import Image
import math
import sys
sys.setrecursionlimit(100000)

def gauss_blur(im, sigma):
    """
    Applies gaussian smoothing to reduce noise
    :param im: the current frame
    :param sigma: the kernel standard deviation, increase for more smoothing
    :return: blurred image
    """
    image = im.load()
    M, N = im.size

    img_new = Image.new(im.mode, (M, N))
    img_px = img_new.load()

    out = Image.new(im.mode, (M, N))
    out_px = out.load()
    if (5 * sigma + 1) % 2 != 0:
        filter_scale = (5 * sigma + 1) // 2
        width = (5 * sigma + 1)
    else:
        filter_scale = (5 * sigma + 2) // 2
        width = (5 * sigma + 2)

    one_D = [0]*width
    one_D[filter_scale] = 1
    for i in range(1, filter_scale + 1):
        val = math.exp(-(i**2) / (2 * sigma**2))
        one_D[filter_scale + i] = val
        one_D[filter_scale - i] = val

    one_D_sum = 1 / sum(one_D)

    for i in range(len(one_D)):
        one_D[i] *= one_D_sum

    # run horz
    for v in range(N):
        for u in range(M):
            total = 0
            for i in range(-filter_scale, filter_scale + 1):
                x = reflected_px(u + i, M)
                total = total + image[x, v] * one_D[i + filter_scale]
            q = int(round(total))
            if q < 0:
                q = 0
            if q > 255:
                q = 255
            img_px[u, v] = q

    #run vert
    for v in range(N):
        for u in range(M):
            total = 0
            for i in range(-filter_scale, filter_scale + 1):
                y = reflected_px(v + i, N)
                total = total + img_px[u, y] * one_D[i + filter_scale]
            q = int(round(total))
            if q < 0:
                q = 0
            if q > 255:
                q = 255
            out_px[u, v] = q

    return out


def convolve(im, kernel):
    """
    Convolves a supplied filter with the image
    :param im: current frame
    :param kernel: filter to convolve with image
    :return: convolved image
    """
    image = im.load()
    kernel = kernel

    M, N = im.size
    img = Image.new("F", (M, N))
    px = img.load()

    height = len(kernel) // 2
    width = len(kernel[0]) // 2

    for v in range(N):
        for u in range(M):
            sum = 0
            for j in range(-height, height + 1):
                for i in range(-width, width + 1):
                    x = reflected_px(u + i, M)
                    y = reflected_px(v + j, N)

                    p = image[x, y]
                    c = kernel[j + height][i + width]
                    sum = sum + c * p

            q = sum
            px[u, v] = q

    return img

def reflected_px(px, size):
    """
    Helper function to convolve to reflect pixels across the border
    in order to handle edge cases
    """
    if px < 0:
        return -px
    if px >= size:
        return 2 * size - px - 2
    return px

def get_Gx(gray_image):
    """
    Calculates the x gradient of each pixel in the frame with the Sobel x filter
    :param gray_image: the blurred frame
    :return: the image map of pixel gradients
    """
    sobel_x = [[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]]
    Gx = convolve(gray_image, sobel_x)
    return Gx

def get_Gy(gray_image):
    """
    Calculates the y gradient of each pixel in the frame with the Sobel y filter
    :param gray_image: the blurred frame
    :return: the image map of pixel gradients
    """
    sobel_y = [[-3, -10, -3], [0, 0, 0], [3, 10, 3]]
    Gy = convolve(gray_image, sobel_y)
    return Gy

def get_edge_strength(image, Gx, Gy):
    """
    Calculates the edge magnitude (strength) of each pixel and stores it in a luminance image
    :param image:
    :param Gx: the corresponding gradient map in the x direction
    :param Gy: the corresponding gradient map in the y direction
    :return: the edge strength map
    """
    out = Image.new("F", image.size)
    M, N = image.size

    max_mag = 0
    for v in range(N):
        for u in range(M):
            val = math.sqrt(math.pow(Gx.getpixel((u, v)), 2) + math.pow(Gy.getpixel((u, v)),2))
            max_mag = max(max_mag, val)
            out.putpixel((u, v), val)

    max_mag = 1 / max_mag

    for v in range(N):
        for u in range(M):
            out.putpixel((u, v), out.getpixel((u,v)) * max_mag)

    return out

def get_orientation_sector(Gx, Gy, u, v):
    """
    Based on the edge orientation, classifies the pixel at (u,v) into the corresponding sector
    :param Gx: the corresponding gradient map in the x direction
    :param Gy: the corresponding gradient map in the y direction
    :param u: row index
    :param v: col index
    :return: the sector the pixel at (u,v) is in
    """
    gx = Gx.getpixel((u, v))
    gy = Gy.getpixel((u, v))
    orientation = math.atan2(gy, gx)
    orientation = math.degrees(math.atan2(gy, gx)) % 180
    if 0 <= orientation <= 22:
        return 0
    elif 23 <= orientation <= 68:
        return 1
    elif 69 <= orientation <= 114:
        return 2
    return 3

# This method is faster as it doesn't repeatedly do as many trig computations
# def get_orientation_sector(Gx, Gy):
#     A = np.array([[math.cos(math.pi / 8), -math.sin(math.pi / 8)], [math.sin(math.pi / 8), math.cos(math.pi / 8)]])
#     M, N = Gx.size
#
#     out = Image.new(Gx.mode, (M, N))
#
#     for v in range(N):
#         for u in range(M):
#             B = np.array([Gx.getpixel((u, v)), Gy.getpixel((u, v))]).T
#             G_next = A @ B
#
#             if G_next[1] < 0:
#                 G_next[0] = -G_next[0]
#                 G_next[1] = -G_next[1]
#             if G_next[0] >= 0:
#                 if G_next[0] > G_next[1]:
#                     out.putpixel((u, v), 0)
#                 else:
#                     out.putpixel((u, v), 1)
#             elif -G_next[0] < G_next[1]:
#                 out.putpixel((u, v), 2)
#             else:
#                 out.putpixel((u,v), 3)
#
#     return out

def non_max_suppression(image, edge_strength, Gx, Gy):
    """
    Thins edges by suppressing non-local max pixel neighbors with the same orientation
    :param image: the current frame
    :param edge_strength: the corresponding edge strength map
    :param Gx: the corresponding gradient map in the x direction
    :param Gy: the corresponding gradient map in the y direction
    :return: The thinned edge map
    """
    M, N = image.size
    t_lo = 0

    maximum_magnitude = Image.new("F", image.size)

    for v in range(1, N - 1):
        for u in range(1, M - 1):
            sector = get_orientation_sector(Gx, Gy, u, v)
            if local_max(edge_strength, sector, t_lo, u, v):
                maximum_magnitude.putpixel((u, v), edge_strength.getpixel((u,v)))

    return maximum_magnitude

def local_max(edge_strength, sector, t_lo, u, v):
    """
    Compares a pixel to its two neighbors with the same edge orientation. If it is greater than both, it is kept, else
    it is suppressed to 0
    :param edge_strength: current pixel's edge strength
    :param sector: current pixel's sector
    :param t_lo: Minimum threshold. If a pixel is under this threshold it is suppressed regardless
    :param u: row index
    :param v: col index
    :return: 1 if local max, 0 otherwise
    """
    val = edge_strength.getpixel((u,v))

    m_l, m_r = 0, 0
    if val < t_lo:
        return 0

    if sector == 0:
        m_l = edge_strength.getpixel((u-1,v))
        m_r = edge_strength.getpixel((u+1,v))
    elif sector == 1:
        m_l = edge_strength.getpixel((u-1,v-1))
        m_r = edge_strength.getpixel((u+1,v+1))
    elif sector == 2:
        m_l = edge_strength.getpixel((u,v-1))
        m_r = edge_strength.getpixel((u,v+1))
    elif sector == 3:
        m_l = edge_strength.getpixel((u-1,v+1))
        m_r = edge_strength.getpixel((u+1,v-1))

    if m_l <= val and val >= m_r:
        return 1
    return 0

def trace_and_threshold(max_mag_map, t_lo, t_hi):
    """
    Applies hysteresis thresholding to the non-maximum suppressed image
    :param max_mag_map: non-maximum suppressed map
    :param t_lo: lower bound threshold
    :param t_hi: upper bound threshold
    :return: the completed edge map
    """
    M, N = max_mag_map.size
    binary_edge_map = Image.new("F", (M, N))
    for v in range(1, N - 1):
        for u in range(1, M - 1):
            if max_mag_map.getpixel((u,v)) >= t_hi and binary_edge_map.getpixel((u,v)) == 0:
                trace_and_threshold_helper(max_mag_map, binary_edge_map, u, v, t_lo)
    return binary_edge_map

def trace_and_threshold_helper(max_mag_map, binary_edge_map, u_0, v_0, t_lo):
    """
    Helper to trace_and_threshold. For each pixel if it is above t_hi it is kept as a strong edge. Recursively, the
    neighbors are traced and if a pixel is inbetween t_hi and t_lo and connected to a strong edge it is kept. Pixels
    less than t_lo are suppressed
    :param max_mag_map: non-maximum suppressed map
    :param binary_edge_map: output edge map to be written to
    :param u_0: col index of the current pixel being traced from
    :param v_0: row index of the current pixel being traced from
    :param t_lo: lower bound threshold
    :return: completed edge map
    """
    M, N = max_mag_map.size
    binary_edge_map.putpixel((u_0,v_0), 1)
    u_l = max(u_0-1, 0)
    u_r = min(u_0+1, M-1)
    v_t = max(v_0-1, 0)
    v_b = min(v_0+1, N-1)
    for v in range(v_t, v_b + 1):
        for u in range(u_l, u_r + 1):
            if binary_edge_map.getpixel((u,v)) == 0 and max_mag_map.getpixel((u,v)) >= t_lo:
                trace_and_threshold_helper(max_mag_map, binary_edge_map, u, v, t_lo)

    return binary_edge_map
