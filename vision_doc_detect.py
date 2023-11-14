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

openai.api_key="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"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"ai-ocr-team-20231017-13e9705ba8ac.json"

def detect_text(content):
    # Google から Vision API 呼び出しを行う
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image, image_context={"language_hints": ["ja", "ja-katakana", "en", "digits"]})
    # response = client.document_text_detection(image=image)

    all_anotations = sort_line_vision.get_extended_annotations(response)
    threshold = sort_line_vision.get_threshold_for_y_difference(all_anotations)
    list_anotations = sort_line_vision.group_annotations(all_anotations, threshold)
    array_result = sort_line_vision.sort_and_combine_grouped_annotations(list_anotations)
    # texts = response.text_annotations

    # # 使用する必要があるデータをグループ化する
    # result = []
    # idx = 0
    # for text in texts:
    #     if idx == 0:
    #         idx += 1
    #         continue
    #     arrVal = []
    #     vertices = [
    #         ast.literal_eval(f"[{vertex.x},{vertex.y}]") for vertex in text.bounding_poly.vertices
    #     ]
    #     arrVal.append(vertices)
    #     arrVal.append(text.description)
    #     result.append(arrVal)

    # # 関数はデータの各行を返します
    # array_result = sort_line.get_all_result(result, content)
    if response.error.message:
        raise Exception(
            "{}\nシステムエラー: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    return array_result