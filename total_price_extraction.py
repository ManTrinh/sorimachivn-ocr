import re

# def get_total_price(response) -> int:
#     texts = response.text_annotations
#     max_x, min_y, max_y, center_y, max_heigth = 0, 0, 0, 0, 0
#     reg_total_price_key = r"合計|クレジット合計|総合計|現計|領収金額|取引金額|ご利用額|料金"
#     reg_total_price_value = r"[¥\\\\][0-9,.]+|\d{1,3}(?:[,.]\d{3})+|[0-9,.]+円|\d{1,9}"
#     text_concat = ""

#     for text in texts[1:]:
#         text_concat += text.description
#         res = re.search(reg_total_price_key, text_concat)
#         if res and res.end() == len(text_concat):
#             vertices = [
#                 "({},{})".format(vertex.x, vertex.y)
#                 for vertex in text.bounding_poly.vertices
#             ]
#             if text.bounding_poly.vertices[3].y - text.bounding_poly.vertices[0].y > max_heigth:
#                 max_x = text.bounding_poly.vertices[1].x                         # 右上のポイントのXの値
#                 min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
#                 max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値
#                 center_y = (max_y - min_y) / 2
#                 max_heigth = max_y - min_y
#                 text_concat = ""

#     total_price, text_concat = "", ""
#     if max_x: # キーがある場合、キーの座標に基づいて検出
#         temp_max_x, target_max_height = 0, 0
#         for text in texts[1:]:
#             target_min_x = text.bounding_poly.vertices[0].x  # 左上のポイントのXの値
#             target_max_x = text.bounding_poly.vertices[1].x  # 右上のポイントのXの値
#             target_min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
#             target_max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値

#             if(((target_min_y <= max_y and target_min_y >= min_y)
#                 or(target_max_y <= max_y and target_max_y >= min_y)
#                 or(target_max_y >= max_y and target_min_y <= min_y))
#                 and target_min_x > max_x                 # 合計の文字より右にある文字
#                 and (target_min_x > temp_max_x or target_max_y - target_min_y > target_max_height)
#             ):
#                 text_concat += text.description
#                 matches = re.findall(reg_total_price_value, text_concat)
#                 if len(matches) == 1 and re.search(matches[0], text_concat).end() == len(text_concat):
#                     total_price = matches[0]
#                     temp_max_x = target_max_x
#                     target_max_height = target_max_y - target_min_y
#                 elif len(matches) > 1:
#                     total_price = matches[len(matches)-1]
#                     temp_max_x = target_max_x
#                     target_max_height = target_max_y - target_min_y

#     else: # キーがない場合、高さが一番大きいバウンディングボックスに基づいて検出
#         temp_max_x, target_max_height = 0, 0
#         for text in texts[1:]:
#             target_min_x = text.bounding_poly.vertices[0].x  # 左上のポイントのXの値
#             target_max_x = text.bounding_poly.vertices[1].x  # 右上のポイントのXの値
#             target_min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
#             target_max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値

#             matches = re.findall(reg_total_price_value, total_price + "¥{}".format(text.description))
#             if not total_price and len(matches) == 1:
#                 total_price = matches[0]
#                 temp_max_x = target_max_x
#                 target_max_height = target_max_y - target_min_y
#             elif len(matches) > 1 and (target_max_y - target_min_y > target_max_height or target_min_x > temp_max_x):
#                 total_price = matches[len(matches)-1]
#                 temp_max_x = target_max_x
#                 target_max_height = target_max_y - target_min_y

#     return total_price


# class TotalAnnotation:
#     def __init__(self, annotation):
#         self.vertex = annotation.bounding_poly.vertices
#         self.text = annotation.description
#         self.avg_y = (self.vertex[0].y + self.vertex[2].y) / 2
#         self.avg_x = abs(self.vertex[0].x + self.vertex[1].x) / 2
#         self.height = ((self.vertex[3].y - self.vertex[1].y) + (self.vertex[2].y - self.vertex[0].y)) / 2
#         # self.start_x = (self.vertex[0].x + self.vertex[3].x) / 2

#     def __repr__(self):
#         result = {
#             'text': self.text,
#             'avg_y': self.avg_y,
#             'avg_x': self.avg_x,
#             'height': self.height,
#         }
#         return result

# def get_total_price_sub(response):
#     texts = response.text_annotations
#     reg_total_price_key = r"合.*計|ク.*レ.*ジ.*ッ.*ト.*合.*計|総.*合.*計|現.*計|領.*収.*金.*額|取.*引.*金.*額|ご.*利.*用.*額|料.*金"
#     reg_total_price_value = r"[¥\\\\][0-9,.]+|\d{1,3}(?:[,.]\d{3})+|[0-9,.]+円|\d{1,9}"
#     arrAnotation = []
#     arrResult = []
#     objTotalKey = None

#     for text in texts[1:]:
#         objTotalVal = TotalAnnotation(text)
#         text = "{}".format(objTotalVal.text)
#         res = re.search(reg_total_price_key, text)
#         if res:
#             objTotalKey = objTotalVal
#             continue
#         arrAnotation.append(objTotalVal)

#     arrAnotation = sorted(arrAnotation, key=lambda x: x.avg_x, reverse=True)
#     for val in arrAnotation:
#         price_check = re.findall(reg_total_price_value, val.text)
#         if abs(objTotalKey.avg_y - val.avg_y) <= 10 and len(price_check) > 0:
#             arrResult.append(val)

#     arrResult = sorted(arrResult, key=lambda x: x['height'], reverse=True)
#     return arrResult[0]

