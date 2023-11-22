import cv2
import numpy as np
from PIL import Image
from io import BytesIO

def gamma_correction(image, gamma = 1.0):
    gamma_values = np.clip((np.arange(256) / 255.0) ** gamma * 255.0, 0, 255).astype(np.uint8)

    return cv2.LUT(image, gamma_values)

def preprocess_image(image):
    # làm tối đường biên
    gamma = gamma_correction(image, 2)

    # Tăng độ sáng, tương phản
    enhanced = cv2.convertScaleAbs(gamma, alpha=1.2, beta=40)

    # Chuyển đen trắng
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Giảm nhiễu
    blurred = cv2.GaussianBlur(~thresh, (5, 5), 0)

    return blurred

def get_horizontal_lines_mask(image, horizontal_size=100):
    # erode và dilate theo chiều ngang
    horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    horizontal = cv2.erode(image.copy(), horizontal_structure, anchor=(-1, -1), iterations=1)
    horizontal = cv2.dilate(horizontal, horizontal_structure, anchor=(-1, -1), iterations=1)

    return horizontal

def get_vertical_lines_mask(image, vertical_size=100):
    # erode va dilate theo chieu dọc
    vertical_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))
    vertical = cv2.erode(image.copy(), vertical_structure, anchor=(-1, -1), iterations=1)
    vertical = cv2.dilate(vertical, vertical_structure, anchor=(-1, -1), iterations=1)

    return vertical

def make_lines_mask(preprocessed, min_horizontal_line_size=100, min_vertical_line_size=100):
    hor_structure = get_horizontal_lines_mask(preprocessed, min_horizontal_line_size)
    hor_mask  = get_vertical_lines_mask(preprocessed, min_vertical_line_size)

    mask = np.zeros((preprocessed.shape[0], preprocessed.shape[1], 1), dtype=np.uint8)
    mask = cv2.bitwise_or(mask, hor_structure)
    mask = cv2.bitwise_or(mask, hor_mask)

    return ~mask

def find_outer_contour(image):
    # Tìm contours trong ảnh
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Tìm contour lớn nhất (contour ngoại vi lớn nhất)
    max_contour = max(contours, key=cv2.contourArea)

    # Tạo ảnh trắng đen để vẽ contours lớn nhất
    result_image = np.zeros_like(image)

    # Vẽ contours lớn nhất lên ảnh trắng đen
    cv2.drawContours(result_image, [max_contour], -1, (255), thickness=cv2.FILLED)

    return result_image

def detect_img(file_byte_data):
    byte_stream = BytesIO(file_byte_data)
    image = Image.open(byte_stream)
    image_array = np.array(image)

    # Resize ảnh
    new_width = int((1000 / image_array.shape[0]) * image_array.shape[1])
    resized_image_array = cv2.resize(image_array, (new_width, 1000))

    # Xử lý ảnh
    pre_processed = preprocess_image(resized_image_array)

    # Tạo mask
    lines_mask = make_lines_mask(pre_processed, min_horizontal_line_size=1800, min_vertical_line_size=500)

    # Cắt ảnh dựa trên khung chứa
    outer_contour = find_outer_contour(lines_mask)
    x, y, w, h = cv2.boundingRect(outer_contour)
    warped_region = resized_image_array[y:y+h, x:x+w]

    _, im_rect_th_encoded = cv2.imencode('.' + image.format, warped_region)
    return im_rect_th_encoded.tobytes()