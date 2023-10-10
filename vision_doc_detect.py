from google.cloud import vision
import sort_line
import os
import ast
import openai

openai.api_key="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"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\HP\Desktop\winter-surf-398202-49a079e22d6e.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r".\winter-surf-398202-49a079e22d6e.json"

def detect_text(path):
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image, image_context={"language_hints": ["ja", "ja-katakana", "en", "digits"]})
    texts = response.text_annotations
    result = []
    content = []
    idx = 0
    for text in texts:
        if idx == 0:
            idx += 1
            continue
        arrVal = []
        vertices = [
            ast.literal_eval(f"[{vertex.x},{vertex.y}]") for vertex in text.bounding_poly.vertices
        ]
        arrVal.append(vertices)
        arrVal.append(text.description)
        # arrVal.append("\n{}".format(",".join(vertices)))
        result.append(arrVal)

    text = sort_line.Get_all_text(result)
    # with open("text.txt", "a", encoding='utf-8') as file:
    #     file.write(path)
    #     file.write("\n")
    #     file.write(text)
    #     file.write("\n")
    #     file.write("-----------------------------------\n")
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    return text
    
# folder_path = "./imgTest/"
# for filename in os.listdir(folder_path):
#     if filename.endswith(".jpg"):
#         file_path = os.path.join(folder_path, filename)
#         detect_text(file_path)
