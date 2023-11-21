import copy
from shapely.geometry import Point, Polygon

# Lấy tọa độ y lớn nhất từ bounding_poly.vertices
def get_y_max(data):
    vertices = data.text_annotations[0].bounding_poly.vertices
    return max(v.y for v in vertices)

# Đặt giá trị 0 cho các tọa độ bị trống
def fill_missing_values(data):
    for annotation in data.text_annotations[1:]:
        for v in annotation.bounding_poly.vertices:
            v.x = v.x if v.x is not None else 0
            v.y = v.y if v.y is not None else 0
    return data

# Đảo ngược tọa độ trục
def invert_axis(data, y_max):
    data = fill_missing_values(data)
    for annotation in data.text_annotations[1:]:
        for v in annotation.bounding_poly.vertices:
            v.y = y_max - v.y
    return data

# Tạo tọa độ của một hình chữ nhật từ hai đoạn thẳng song song
def create_rect_coordinates(line1, line2):
    return [
        [line1['xMin'], line1['yMin']],
        [line1['xMax'], line1['yMax']],
        [line2['xMax'], line2['yMax']],
        [line2['xMin'], line2['yMin']]
    ]

def get_bounding_polygon(merged_array):
    after_array = []

    for i, element in enumerate(merged_array):
        extended_info = [element]

        vertices = element.bounding_poly.vertices

        # Tính toán chiều cao trung bình của bounding polygon
        h1 = vertices[0].y - vertices[3].y
        h2 = vertices[1].y - vertices[2].y
        avg_height = max(h1, h2) * 0.6

        # Tạo hai đường chữ nhật dựa trên các đỉnh của bounding polygon
        arr = []
        arr.append(vertices[1])
        arr.append(vertices[0])
        line1 = get_rectangle(copy.deepcopy(arr), avg_height, True)

        arr = []
        arr.append(vertices[2])
        arr.append(vertices[3])
        line2 = get_rectangle(copy.deepcopy(arr), avg_height, False)

        # line_num: index
        # match   :
        # matched : thuộc tính kiểm tra ghép nối với phần tử khác
        # bigbb   : tọa độ 4 đỉnh của khung lớn bao bên ngoài
        extended_info.append({
            'line_num': i,
            'match': [],
            'matched': False,
            'bigbb': create_rect_coordinates(line1, line2)
        })

        after_array.append(extended_info)

    return after_array

def get_rectangle(vertices, avg_height, is_add):
    avg_height = round(avg_height)
    # Cập nhật giá trị y tương ứng
    if is_add:
        vertices[1].y += avg_height
        vertices[0].y += avg_height
    else:
        vertices[1].y -= avg_height
        vertices[0].y -= avg_height

    y_diff = vertices[1].y - vertices[0].y
    x_diff = vertices[1].x - vertices[0].x

    # Tính toán độ dốc của đoạn thẳng
    gradient = 0 if x_diff == 0 else y_diff / x_diff

    x_thresh_min = 1
    x_thresh_max = 2000

    # Xác định giá trị y tối thiểu và tối đa dựa trên độ dốc và ngưỡng x
    if gradient == 0:
        y_min = vertices[0].y
        y_max = vertices[0].y
    else:
        y_min = vertices[0].y - (gradient * (vertices[0].x - x_thresh_min))
        y_max = vertices[0].y + (gradient * (x_thresh_max - vertices[0].x))

    # Làm tròn giá trị
    y_min = round(y_min)
    y_max = round(y_max)

    return {'xMin': x_thresh_min, 'xMax': x_thresh_max, 'yMin': y_min, 'yMax': y_max}

# Kiểm tra xem một điểm có nằm trong một đa giác không
def is_point_inside_polygon(point, polygon):
    point = Point(point[0], point[1])
    polygon = Polygon(polygon)
    return point.within(polygon)

def combine_bounding_polygon(merged_array):
    for i in range(len(merged_array)):
        big_bb = merged_array[i][1]['bigbb']

        for k in range(i, len(merged_array)):
            # Kiểm tra xem phần tử có khác với phần tử hiện tại và chưa được ghép nối chưa
            if k != i and not merged_array[k][1]['matched']:
                inside_count = 0

                for j in range(4):
                    coordinate = merged_array[k][0].bounding_poly.vertices[j]

                    # Kiểm tra xem đỉnh có nằm trong bounding box lớn không
                    if is_point_inside_polygon([coordinate.x, coordinate.y], big_bb):
                        inside_count += 1

                # Nếu tất cả 4 đỉnh của phần tử k nằm trong bounding box lớn
                if inside_count == 4:
                    # matchLineNum: match với phần tử có index nào
                    merged_array[i][1]['match'].append({'matchLineNum': k})
                    # Đánh dấu phần tử k là đã ghép nối
                    merged_array[k][1]['matched'] = True