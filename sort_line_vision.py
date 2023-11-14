import re
from operator import attrgetter
import numpy as np

class ExtendedAnnotation:
    def __init__(self, annotation):
        self.vertex = annotation.bounding_poly.vertices
        self.text = annotation.description
        self.avg_y = (self.vertex[0].y + self.vertex[1].y + self.vertex[2].y + self.vertex[3].y) / 4
        self.height = ((self.vertex[3].y - self.vertex[1].y) + (self.vertex[2].y - self.vertex[0].y)) / 2
        self.start_x = (self.vertex[0].x + self.vertex[3].x) / 2

    def __repr__(self):
        return '{' + self.text + ', ' + str(self.avg_y) + ', ' + str(self.height) + ', ' + str(self.start_x) + '}'
    
def get_extended_annotations(response):
    extended_annotations = []
    for annotation in response.text_annotations:
        extended_annotations.append(ExtendedAnnotation(annotation))
    # delete last item, as it is the whole text I guess.
    del extended_annotations[0]
    return extended_annotations

def get_threshold_for_y_difference(annotations):
    annotations.sort(key=attrgetter('avg_y'))
    differences = []
    for i in range(0, len(annotations)):
        if i == 0:
            continue
        differences.append(abs(annotations[i].avg_y - annotations[i - 1].avg_y))
    # Sử dụng hàm sum() để cộng tất cả các giá trị trong danh sách
    total_sum = sum(differences)
    
    # Sử dụng hàm len() để lấy số lượng phần tử trong danh sách
    list_length = len(differences)
    
    # Tính trung bình
    average = total_sum / list_length    
    # return np.std(differences)
    return np.std(differences) - average

def group_annotations(annotations, threshold):
    annotations.sort(key=attrgetter('avg_y'))
    line_index = 0
    text = [[]]
    for i in range(0, len(annotations)):
        if i == 0:
            text[line_index].append(annotations[i])
            continue
        y_difference = abs(annotations[i].avg_y - annotations[i - 1].avg_y)
        if y_difference > threshold:
            line_index = line_index + 1
            text.append([])
        text[line_index].append(annotations[i])
    return text

def sort_and_combine_grouped_annotations(annotation_lists):
    grouped_list = []
    for annotation_group in annotation_lists:
        annotation_group.sort(key=attrgetter('start_x'))
        texts = (o.text for o in annotation_group)
        texts = ''.join(texts)
        texts = re.sub(r'\s([-;:?.!](?:\s|$))', r'\1', texts)
        grouped_list.append(texts)
    return grouped_list

# respone = read_image(r"C:\Users\HP\Desktop\FFTest\GoogleAPI\img_test.png")

