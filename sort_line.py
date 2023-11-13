# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : sort_line.py
#  Function    : 行ごとに短い
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/

import cv2
import numpy as np
# Data Example
# bounding_boxes = [
#     [[(155, 260), (1401, 260), (1401, 2635), (155, 2635)], "Text1"],
#     [[(414, 270), (1091, 260), (1094, 501), (418, 511)],"Text2"],
#     [[(463, 535), (496, 535), (496, 585), (463, 585)],"Text3"],
#     [[(512, 534), (764, 533), (764, 584), (512, 585)],"Text4"],
#     [[(797, 532), (1019, 531), (1019, 582), (797, 583)],"Text5"]
# ]

# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : sort_line.py
#  Function    : 行が同じ行にあるかどうかを確認します
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/
def are_boxes_on_same_row(box1, box2, tolerance):
    # center_y1 = ((box1[0][1]) + (box1[1][1])) / 2
    # center_y2 = ((box2[0][1]) + (box2[1][1])) / 2
    center_y1 = ((box1[1][1]))
    center_y2 = ((box2[1][1]))    
    # tolerance = ((box1[1][1])) + 
    # h1 = (box1[2][1]) - (box1[0][1])
    # h2 = (box2[2][1]) - (box2[0][1])

    return abs(center_y1 - center_y2) < tolerance


def find_text_threshold(image):
    # Chuyển ảnh sang ảnh đen trắng
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Phát hiện cạnh sử dụng phương pháp Canny
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Tính toán ngưỡng trung bình dựa trên giá trị pixel trong vùng quan tâm
    roi = gray[edges != 0]
    average_threshold = np.mean(roi)

    # Chuyển đổi ngưỡng từ kiểu float sang kiểu int
    int_threshold = int(average_threshold)
    if int_threshold < 100:
        int_threshold = 20
    else:
        int_threshold = 10
    return int_threshold

# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : sort_line.py
#  Function    : 行データの配列を返します
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/
def get_all_result(bounding_boxes, content):
    # Chuyển đổi chuỗi byte thành mảng numpy
    np_data = np.frombuffer(content, np.uint8)

# Đọc hình ảnh từ mảng numpy
    image = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    thresh_hold = find_text_threshold(image)

    sorted_boxes = []
    for box in bounding_boxes:
        added = False
        for row in sorted_boxes:
            boxTmp = box[0]
            boxRowTmp = row[0][0]
            if are_boxes_on_same_row(boxTmp, boxRowTmp, thresh_hold):
                row.append(box)
                added = True
                break
        if not added:
            sorted_boxes.append([box])

    result = []
    threshold_x_distance = 30
    sorted_coordinates = sorted(sorted_boxes, key=lambda y: y[0][0][0][1])
    for group in sorted_coordinates:
        sorted_coordinates_colums = sorted(group, key=lambda x: x[0][0][0])
        one_row_arr = []
        current_group = []
        height_text_row = []

        for box in sorted_coordinates_colums:
            if not current_group:
                current_group.append(box)
            else:
                prev_x = current_group[-1][0][1][0]
                curr_x = box[0][0][0]
                if curr_x - prev_x <= threshold_x_distance:
                    current_group.append(box)
                else:
                    grouped_values = "".join(box[1] for box in current_group)
                    one_row_arr.append(grouped_values)
                    current_group = [box]

        if current_group:
            grouped_values = "".join(box[1] for box in current_group)
            one_row_arr.append(grouped_values)

        one_row_val = " ".join(one_row_arr)
        height = abs(group[0][0][2][1] - group[0][0][0][1])
        height_text_row.append(one_row_val)
        height_text_row.append(height)
        result.append(height_text_row)

    return result