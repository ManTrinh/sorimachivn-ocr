# import argparse
# from enum import Enum

# from google.cloud import vision
# from PIL import Image, ImageDraw
# import os
# import openai
# import cv2
# import numpy as np
# openai.api_key="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"

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\HP\Desktop\winter-surf-398202-49a079e22d6e.json"


# class FeatureType(Enum):
#     PAGE = 1
#     BLOCK = 2
#     PARA = 3
#     WORD = 4
#     SYMBOL = 5


# def draw_boxes(image, bounds, color):
#     """Draws a border around the image using the hints in the vector list.

#     Args:
#         image: the input image object.
#         bounds: list of coordinates for the boxes.
#         color: the color of the box.

#     Returns:
#         An image with colored bounds added.
#     """
#     # Đọc ảnh từ file
#     image = cv2.imread(image.filename)
#     # Màu của đa giác (BGR)
#     color = (0, 128, 0)  # Màu đỏ (BGR)

#     # Độ dày của đường viền đa giác
#     thickness = 2
#     # draw = ImageDraw.Draw(image)

#     for bound in bounds:
#         # draw.polygon(
#         #     [
#         #         bound.vertices[0].x,
#         #         bound.vertices[0].y,
#         #         bound.vertices[1].x,
#         #         bound.vertices[1].y,
#         #         bound.vertices[2].x,
#         #         bound.vertices[2].y,
#         #         bound.vertices[3].x,
#         #         bound.vertices[3].y,
#         #     ],
#         #     None,
#         #     color,
#         # )
#         # Chuyển danh sách tọa độ thành một mảng numpy
#         polygon_coordinates = [
#             (bound.vertices[0].x,
#             bound.vertices[0].y),
#             (bound.vertices[1].x,
#             bound.vertices[1].y),
#             (bound.vertices[2].x,
#             bound.vertices[2].y),
#             (bound.vertices[3].x,
#             bound.vertices[3].y)
#         ],
#         polygon_coordinates = np.array(polygon_coordinates)
#         # Vẽ đa giác
#         cv2.polylines(image, [polygon_coordinates], isClosed=True, color=color, thickness=thickness)
#     # Đợi một phím bấm và sau đó đóng cửa sổ hiển thị
#     cv2.imwrite("test.jpg", image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()    
#     # return image


# def get_document_bounds(image_file, feature):
#     """Finds the document bounds given an image and feature type.

#     Args:
#         image_file: path to the image file.
#         feature: feature type to detect.

#     Returns:
#         List of coordinates for the corresponding feature type.
#     """
#     client = vision.ImageAnnotatorClient()

#     bounds = []

#     with open(image_file, "rb") as image_file:
#         content = image_file.read()

#     image = vision.Image(content=content)

#     response = client.document_text_detection(image=image, image_context={"language_hints": ["ja", "ja-katakana", "en", "digits"]})
#     document = response.full_text_annotation

#     # Collect specified feature bounds by enumerating all document features
#     for page in document.pages:
#         for block in page.blocks:
#             for paragraph in block.paragraphs:
#                 for word in paragraph.words:
#                     for symbol in word.symbols:
#                         if feature == FeatureType.SYMBOL:
#                             bounds.append(symbol.bounding_box)

#                     if feature == FeatureType.WORD:
#                         bounds.append(word.bounding_box)

#                 if feature == FeatureType.PARA:
#                     bounds.append(paragraph.bounding_box)

#             if feature == FeatureType.BLOCK:
#                 bounds.append(block.bounding_box)

#     # The list `bounds` contains the coordinates of the bounding boxes.
#     return bounds




# def render_doc_text(filein, fileout):
#     """Outlines document features (blocks, paragraphs and words) given an image.

#     Args:
#         filein: path to the input image.
#         fileout: path to the output image.
#     """
#     image = Image.open(filein)
#     # bounds = get_document_bounds(filein, FeatureType.BLOCK)
#     # draw_boxes(image, bounds, "blue")
#     # bounds = get_document_bounds(filein, FeatureType.PARA)
#     # draw_boxes(image, bounds, "red")
#     bounds = get_document_bounds(filein, FeatureType.BLOCK)
#     draw_boxes(image, bounds, "yellow")

#     # if fileout != 0:
#     #     image.save(fileout)
#     # else:
#     #     image.show()


# if __name__ == "__main__":

#     render_doc_text("./imgTest/Man1.jpg", "tmp.png")

import time

# Lấy thời điểm bắt đầu
start_time = time.time()
import json
import re
from google.cloud import vision
from google.cloud import storage
import os
import openai
openai.api_key="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"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\HP\Desktop\winter-surf-398202-49a079e22d6e.json"

def async_detect_document(gcs_source_uri, gcs_destination_uri):
    """OCR with PDF/TIFF as source files on GCS"""

    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"

    # How many pages should be grouped into each json output file.
    batch_size = 1

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size
    )

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config, output_config=output_config
    )

    operation = client.async_batch_annotate_files(requests=[async_request])

    print("Waiting for the operation to finish.")
    operation.result(timeout=420)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    match = re.match(r"gs://([^/]+)/(.+)", gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)

    # List objects with the given prefix, filtering out folders.
    blob_list = [
        blob
        for blob in list(bucket.list_blobs(prefix=prefix))
        if not blob.name.endswith("/")
    ]
    print("Output files:")
    for blob in blob_list:
        print(blob.name)

    # Process the first output file from GCS.
    # Since we specified batch_size=2, the first response contains
    # the first two pages of the input file.
    bCheck = False
    for out in blob_list:
        if bCheck == False:
            bCheck = True
            continue

        json_string = out.download_as_bytes().decode("utf-8")
        response = json.loads(json_string)

        # The actual response for the first page of the input file.
        first_page_response = response["responses"][0]
        annotation = first_page_response["fullTextAnnotation"]

        # Here we print the full text from the first page.
        # The response contains more information:
        # annotation/pages/blocks/paragraphs/words/symbols
        # including confidence scores and bounding boxes
        print("--------------------------------\n")
        print(annotation["text"]) 

    # output = blob_list[1]
    # json_string = output.download_as_bytes().decode("utf-8")
    # response = json.loads(json_string)

    # # The actual response for the first page of the input file.
    # first_page_response = response["responses"][0]
    # annotation = first_page_response["fullTextAnnotation"]

    # # Here we print the full text from the first page.
    # # The response contains more information:
    # # annotation/pages/blocks/paragraphs/words/symbols
    # # including confidence scores and bounding boxes
    # print("Full text:\n")
    # print(annotation["text"])
async_detect_document("gs://man_test/man_test_pdf2.pdf", "gs://man_test/man_test")
# Lấy thời điểm kết thúc
end_time = time.time()
# Tính thời gian thực thi bằng cách trừ thời điểm bắt đầu từ thời điểm kết thúc
execution_time = end_time - start_time

# In thời gian thực thi
print(f"Thời gian thực thi: {execution_time} giây")    
