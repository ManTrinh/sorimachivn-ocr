import re

def get_total_price(response) -> int:
    texts = response.text_annotations
    max_x, min_y, max_y, center_y, max_heigth = 0, 0, 0, 0, 0
    reg_total_price_key = [r"合計|クレジット合計|総合計|領収金額|取引金額|ご利用額|請求額", r"現計", r"料金"]
    reg_price_character = r"(^(\d{1,3}(?:\,\d{3})*)$|[,.¥円])+?"
    reg_price_value = r"(?:\¥)?(?:\d{1,3}(?:,\d{3})*(?:\,\d{3})?|(?:\d{4}(?:,\d{3})*(?:\,\d{3})?))|(?:\$)\d+(?:,\d{3})"
    text_concat = ""
    match_index = 0

    for text in texts[1:]:
        text_concat += text.description
        index = 1
        for pattern in reg_total_price_key:
            res = re.search(pattern, text_concat)
            if res and res.end() == len(text_concat):
                vertices = [
                    "({},{})".format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices
                ]
                if match_index == 0 or index < match_index or (index == match_index and text.bounding_poly.vertices[3].y - text.bounding_poly.vertices[0].y > max_heigth):
                    max_x = text.bounding_poly.vertices[1].x                         # 右上のポイントのXの値
                    min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
                    max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値
                    center_y = (max_y - min_y) / 2
                    max_heigth = max_y - min_y
                    text_concat = ""
                    match_index = index
                    break
            index += 1

    total_price, text_concat = "", ""
    if max_x: # キーがある場合、キーの座標に基づいて検出
        temp_max_x, target_max_height, eccentricity = 0, 0, 0
        for text in texts[1:]:
            target_min_x = text.bounding_poly.vertices[0].x  # 左上のポイントのXの値
            target_max_x = text.bounding_poly.vertices[1].x  # 右上のポイントのXの値
            target_min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
            target_max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値
            target_center_y = (target_max_y - target_min_y) / 2

            if(((target_min_y <= max_y and target_min_y >= min_y)
                or(target_max_y <= max_y and target_max_y >= min_y)
                or(target_max_y >= max_y and target_min_y <= min_y))
                and target_min_x > max_x                 # 合計の文字より右にある文字
                and (target_min_x > temp_max_x or target_max_y - target_min_y > target_max_height or abs(center_y - target_center_y) < eccentricity)
                and re.match(reg_price_character, text.description)
                and (not total_price or total_price[0] != "¥" or total_price[0] == text.description[0])
            ):
                text_concat += text.description
                matches = re.findall(reg_price_value, text_concat)
                if len(matches) == 1 and re.search(matches[0], text_concat).end() == len(text_concat):
                    total_price = text_concat = matches[0]
                    temp_max_x = target_max_x
                    target_max_height = target_max_y - target_min_y 
                    eccentricity = abs(center_y - target_center_y)
                elif len(matches) > 1:
                    total_price = text_concat = matches[len(matches)-1]
                    temp_max_x = target_max_x
                    target_max_height = target_max_y - target_min_y 
                    eccentricity = abs(center_y - target_center_y)

    else: # キーがない場合、高さが一番大きいバウンディングボックスに基づいて検出
        temp_max_x, target_max_height = 0, 0
        for text in texts[1:]:
            target_min_x = text.bounding_poly.vertices[0].x  # 左上のポイントのXの値
            target_max_x = text.bounding_poly.vertices[1].x  # 右上のポイントのXの値
            target_min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
            target_max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値

            if((target_min_x > temp_max_x or target_max_y - target_min_y > target_max_height)
                and re.match(reg_price_character, text.description)
                and (not total_price or total_price[0] != "¥" or total_price[0] == text.description[0])
            ):
                text_concat += text.description
                matches = re.findall(reg_price_value, text_concat)
                if len(matches) == 1 and re.search(matches[0], text_concat).end() == len(text_concat):
                    total_price = text_concat = matches[0]
                    temp_max_x = target_max_x
                    target_max_height = target_max_y - target_min_y
                elif len(matches) > 1:
                    total_price = text_concat = matches[len(matches)-1]
                    temp_max_x = target_max_x
                    target_max_height = target_max_y - target_min_y

    return total_price