import matplotlib.pyplot as plt
import conditernHelp
import copy

def get_merged_lines(lines, raw_text):
    # các từ được gộp theo từng dòng
    merged_array = []

    while len(lines) != 0:
        current_line = lines.pop()
        init_line = current_line
        is_first_word = True

        merged_element = None

        while True:
            # từ đang được xử lý
            w_element = raw_text.pop()
            if w_element is None:
                break

            w = w_element.description
            index = current_line.find(w)

            # không tìm thấy từ trong chuỗi hiện tại
            if index == -1:
                raw_text.insert(0, w_element)
                continue

            current_line = current_line[index + len(w):]
            # là từ đầu tiên của dòng ?
            if is_first_word:
                is_first_word = False
                merged_element = w_element

            # dòng đã xử lý tất cả kí tự
            if not current_line:
                merged_element.description = init_line
                merged_element.bounding_poly.vertices[1] = w_element.bounding_poly.vertices[1]
                merged_element.bounding_poly.vertices[2] = w_element.bounding_poly.vertices[2]
                merged_array.append(merged_element)
                break

    return merged_array

def move_yen_to_end(input_string):
    # Kiểm tra xem chuỗi bắt đầu bằng '¥'
    if input_string.startswith('¥'):
        # Tìm vị trí đầu tiên của số sau '¥'
        index = 1
        while index < len(input_string) and input_string[index].isdigit():
            index += 1

        # Tách '¥' và số liền kề sau nó
        yen_part = input_string[:index]
        remaining_part = input_string[index:]

        # Chuyển '¥' và số về cuối chuỗi
        result_string = remaining_part + ' ' + yen_part
        return result_string

    return input_string

def arrange_words_in_order(merged_array, k):
    merged_line = ''
    line = merged_array[k][1]['match']

    for i in range(len(line)):
        index = line[i]['matchLineNum']
        matched_word_for_line = merged_array[index][0].description

        main_x = merged_array[k][0].bounding_poly.vertices[1].x
        compare_x = merged_array[index][0].bounding_poly.vertices[1].x

        if compare_x > main_x:
            merged_line = merged_array[k][0].description + ' ' + matched_word_for_line
        else:
            merged_line = matched_word_for_line + ' ' + merged_array[k][0].description

    # return move_yen_to_end(merged_line)
    return merged_line

def construct_line_with_bounding_polygon(merged_array):
    final_array = []

    for i in range(len(merged_array)):
        if not merged_array[i][1]['matched']:
            if len(merged_array[i][1]['match']) == 0:
                final_array.append(merged_array[i][0].description)
            else:
                final_array.append(arrange_words_in_order(merged_array, i))

    return final_array

def get_sorted_lines(data):
    # Tọa độ y lơn nhất của khung ngoài cùng
    y_max = conditernHelp.get_y_max(data)

    data = conditernHelp.invert_axis(data, y_max)
    # Các từ được xác định theo từng dòng
    lines = data.text_annotations[0].description.split('\n')
    lines = list(reversed(lines))
    # Danh sách các từ bao gồm tọa độ
    raw_text = copy.copy(data.text_annotations)
    raw_text = list(reversed(raw_text))
    raw_text.pop(-1)

    merged_array = get_merged_lines(lines, raw_text)

    new_data = conditernHelp.get_bounding_polygon(merged_array)

    conditernHelp.combine_bounding_polygon(new_data)

    return construct_line_with_bounding_polygon(new_data)