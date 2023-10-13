# # Dữ liệu bounding box ví dụ
# bounding_boxes = [
#     [[(155, 260), (1401, 260), (1401, 2635), (155, 2635)], "Text1"],
#     [[(414, 270), (1091, 260), (1094, 501), (418, 511)],"Text2"],
#     [[(463, 535), (496, 535), (496, 585), (463, 585)],"Text3"],
#     [[(512, 534), (764, 533), (764, 584), (512, 585)],"Text4"],
#     [[(797, 532), (1019, 531), (1019, 582), (797, 583)],"Text5"]
# ]

def are_boxes_on_same_row(box1, box2, tolerance=10):
    center_y1 = ((box1[0][1]) + (box1[1][1])) / 2
    center_y2 = ((box2[0][1]) + (box2[1][1])) / 2
    # So sánh giá trị y trung tâm với khoảng sai số (tolerance)
    return abs(center_y1 - center_y2) <= tolerance

# Sắp xếp các bounding box theo hàng
def Get_all_text(bounding_boxes):
    sorted_boxes = []
    for box in bounding_boxes:
        added = False
        # Kiểm tra xem box có nằm cùng hàng với bất kỳ bounding box nào trong sorted_boxes không
        for row in sorted_boxes:
            boxTmp = box[0]
            boxRowTmp = row[0][0]
            if are_boxes_on_same_row(boxTmp, boxRowTmp):
                row.append(box)
                added = True
                break
        # Nếu không nằm cùng hàng với bất kỳ bounding box nào trong sorted_boxes, tạo một hàng mới
        if not added:
            sorted_boxes.append([box])

    # Kết quả sắp xếp
    result = []
    threshold_x_distance = 30
    # Sort theo y để sắp xếp top xuống bottom
    sorted_coordinates = sorted(sorted_boxes, key=lambda y: y[0][0][0][1])
    for group in sorted_coordinates:
        # sort theo x sắp xếp từ left sang right
        sorted_coordinates_colums = sorted(group, key=lambda x: x[0][0][0])
        # arr text chung 1 dòng
        one_row_arr = []
        # arr text neu tọa độ gần nhau
        current_group = []
        for box in sorted_coordinates_colums:
            # one_row_arr.append(box[1])
            if not current_group:
                current_group.append(box)
            else:
                # So sánh tọa độ x1 vs x0 với ngưỡng khoảng cách
                prev_x = current_group[-1][0][1][0] # Lay tọa độ x1 của phần tử cuối
                curr_x = box[0][0][0] # Tọa độ x0 của phần tử đầu kế tiếp
                # TH1
                if curr_x - prev_x <= threshold_x_distance:
                    current_group.append(box)
                else:
                    # Gom các phần tử có tọa độ x gần nhau lại thành một chuỗi từ current_group trước đó
                    grouped_values = "".join(box[1] for box in current_group)
                    one_row_arr.append(grouped_values)
                    current_group = [box]
        # Xử lý các phần tử còn lại trong current_group nếu không rơi vào 
        if current_group:
            grouped_values = "".join(box[1] for box in current_group)
            one_row_arr.append(grouped_values)

        one_row_val = " ".join(one_row_arr)
        result.append(one_row_val)

    all_text = "\n".join(result)
    return all_text