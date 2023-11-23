# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : vision_doc_detect.py
#  Function    : 画像を文字列に検出
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/
from google.cloud import vision
# import sort_line
import os
import ast
import openai
import sort_line_vision
import pre_process_img

openai.api_key="c252ff0dae336f2155635074bcb03b81fb45aad0"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"ai-ocr-team-20231017-c252ff0dae33.json"

def detect_text(content):
    # Google から Vision API 呼び出しを行う
    client = vision.ImageAnnotatorClient()
    # content = pre_process_img.detect_img(content)
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image, image_context={"language_hints": ["ja", "ja-katakana", "en", "digits"]})
    # response = client.document_text_detection(image=image)
    gradient = sort_line_vision.getGradientFromTextAnnotations(response.text_annotations)
    all_anotations = sort_line_vision.get_extended_annotations(response)
    threshold = sort_line_vision.get_threshold_for_y_difference(all_anotations, gradient)
    list_anotations = sort_line_vision.group_annotations(all_anotations, threshold, gradient)
    array_result = sort_line_vision.sort_and_combine_grouped_annotations(list_anotations)

    if response.error.message:
        raise Exception(
            "{}\nシステムエラー: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
# 2023-11-22 TienQuach 修正    
    result = {
        'array_text': array_result,
        'response': response
    }
# 2023-11-22 TienQuach 修正    
    return result