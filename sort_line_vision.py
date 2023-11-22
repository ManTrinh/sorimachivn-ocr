# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : sort_line.py
#  Function    : 行ごとに短い
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/

import re
from operator import attrgetter
import numpy as np
import math

class ExtendedAnnotation:
    def __init__(self, annotation):
        self.vertex = annotation.bounding_poly.vertices
        self.text = annotation.description
        # self.avg_y = (self.vertex[0].y + self.vertex[1].y + self.vertex[2].y + self.vertex[3].y) / 4
        self.avg_y = (self.vertex[0].y + self.vertex[2].y) / 2
        self.height = ((self.vertex[3].y - self.vertex[1].y) + (self.vertex[2].y - self.vertex[0].y)) / 2
        self.start_x = self.vertex[0].x

    def __repr__(self):
        return '{' + self.text + ', ' + str(self.avg_y) + ', ' + str(self.height) + ', ' + str(self.start_x) + '}'
    
def get_extended_annotations(response):
    extended_annotations = []
    for annotation in response.text_annotations:
        extended_annotations.append(ExtendedAnnotation(annotation))

    # total_x = sum(annotation.avg_y for annotation in extended_annotations[1:])
    # first_y = abs(extended_annotations[0].avg_y - (total_x / (len(extended_annotations) - 1)))

    del extended_annotations[0]
    # extend_val = {
    #     'extended_annotations': extended_annotations,
    #     'first_y': first_y
    # }
    # for annotation in extended_annotations:
    #     annotation.avg_y = annotation.avg_y - first_y
    return extended_annotations

# レシートの傾きを求める
def getGradientFromTextAnnotations(textAnnotations):
    if(len(textAnnotations) < 1):
        return 0

    gradients = []
    for annotation in textAnnotations:
        boxes = annotation.bounding_poly.vertices
        if len(boxes) < 2:
            continue
        if 'x' not in boxes[0] \
            or 'y' not in boxes[0] \
            or 'x' not in boxes[1] \
            or 'y' not in boxes[1] :
            continue
        x1,y1 = int(boxes[0].x),int(boxes[0].y)
        x2,y2 = int(boxes[1].x),int(boxes[1].y)

        # 縦長のバウンディングボックスは無視
        if abs(y2-y1) > abs(x2-x1):
            continue

        gradient = math.atan2(y2-y1,x2-x1)
        gradients.append(gradient)
    gradients.pop(0)
    if len(gradients)==0:
        return 0

    result = np.average(gradients)
    return result

def get_threshold_for_y_difference(annotations, gradient):
    annotations.sort(key=attrgetter('avg_y'))
    angle = abs(gradient)
    differences = []
    for i in range(0, len(annotations)):
        if i == 0:
            continue
        differences.append(abs( (angle * annotations[i].avg_y) - (angle * annotations[i - 1].avg_y) ))

    total_sum = sum(differences)
    list_length = len(differences)
    average = total_sum / list_length   

    return np.std(differences) - average

def group_annotations(annotations, threshold, gradient):
    annotations.sort(key=attrgetter('avg_y'))
    angle = abs(gradient)
    line_index = 0
    text = [[]]
    for i in range(0, len(annotations)):
        if i == 0:
            text[line_index].append(annotations[i])
            continue
        y_difference = abs((angle * annotations[i].avg_y) - (angle * annotations[i - 1].avg_y) )
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
        texts = ' '.join(texts)
        texts = re.sub(r'\s([-;:?.!](?:\s|$))', r'\1', texts)
        grouped_list.append(texts)
    return grouped_list


