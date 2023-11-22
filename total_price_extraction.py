import re

def get_total_price(response) -> int:
    texts = response.text_annotations
    max_x, min_y, max_y, center_y, max_heigth = 0, 0, 0, 0, 0
    reg_total_price_key = r"合計|クレジット合計|総合計|現計|領収金額|取引金額|ご利用額|料金"
    reg_total_price_value = r"[¥\\\\][0-9,.]+|\d{1,3}(?:[,.]\d{3})+|[0-9,.]+円|\d{1,9}"
    text_concat = ""

    for text in texts[1:]:
        text_concat += text.description
        res = re.search(reg_total_price_key, text_concat)
        if res and res.end() == len(text_concat):
            vertices = [
                "({},{})".format(vertex.x, vertex.y)
                for vertex in text.bounding_poly.vertices
            ]
            if text.bounding_poly.vertices[3].y - text.bounding_poly.vertices[0].y > max_heigth:
                max_x = text.bounding_poly.vertices[1].x                         # 右上のポイントのXの値
                min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
                max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値
                center_y = (max_y - min_y) / 2
                max_heigth = max_y - min_y
                text_concat = ""

    total_price, text_concat = "", ""
    if max_x: # キーがある場合、キーの座標に基づいて検出
        temp_max_x, target_max_height = 0, 0
        for text in texts[1:]:
            target_min_x = text.bounding_poly.vertices[0].x  # 左上のポイントのXの値
            target_max_x = text.bounding_poly.vertices[1].x  # 右上のポイントのXの値
            target_min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
            target_max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値

            if(((target_min_y <= max_y and target_min_y >= min_y)
                or(target_max_y <= max_y and target_max_y >= min_y)
                or(target_max_y >= max_y and target_min_y <= min_y))
                and target_min_x > max_x                 # 合計の文字より右にある文字
                and (target_min_x > temp_max_x or target_max_y - target_min_y > target_max_height)
            ):
                text_concat += text.description
                matches = re.findall(reg_total_price_value, text_concat)
                if len(matches) == 1 and re.search(matches[0], text_concat).end() == len(text_concat):
                    total_price = matches[0]
                    temp_max_x = target_max_x
                    target_max_height = target_max_y - target_min_y
                elif len(matches) > 1:
                    total_price = matches[len(matches)-1]
                    temp_max_x = target_max_x
                    target_max_height = target_max_y - target_min_y

    else: # キーがない場合、高さが一番大きいバウンディングボックスに基づいて検出
        temp_max_x, target_max_height = 0, 0
        for text in texts[1:]:
            target_min_x = text.bounding_poly.vertices[0].x  # 左上のポイントのXの値
            target_max_x = text.bounding_poly.vertices[1].x  # 右上のポイントのXの値
            target_min_y = min(vertex.y for vertex in text.bounding_poly.vertices)  # 左上のポイントのYの値
            target_max_y = max(vertex.y for vertex in text.bounding_poly.vertices)  # 右下のポイントのYの値

            matches = re.findall(reg_total_price_value, total_price + "¥{}".format(text.description))
            if not total_price and len(matches) == 1:
                total_price = matches[0]
                temp_max_x = target_max_x
                target_max_height = target_max_y - target_min_y
            elif len(matches) > 1 and (target_max_y - target_min_y > target_max_height or target_min_x > temp_max_x):
                total_price = matches[len(matches)-1]
                temp_max_x = target_max_x
                target_max_height = target_max_y - target_min_y

    return total_price

    
    # document = response.full_text_annotation
    # bounds = []
    # for page in document.pages:
    #     for block in page.blocks:
    #         for paragraph in block.paragraphs:
    #             for word in paragraph.words:
    #                 for symbol in word.symbols: #左上のBBOXの情報をx,yに集約
    #                     text_concat += symbol.text
    #                     res = re.search(reg_total_price_key, text_concat)
    #                     if res and res.end() == len(text_concat):
    #                         if symbol.bounding_box.vertices[3].y - symbol.bounding_box.vertices[0].y > max_heigth:
    #                             max_x = symbol.bounding_box.vertices[1].x  # 右上のポイントのXの値
    #                             min_y = symbol.bounding_box.vertices[0].y  # 左上のポイントのYの値
    #                             max_y = symbol.bounding_box.vertices[3].y  # 右下のポイントのYの値
    #                             max_heigth = max_y - min_y
    #                             text_concat = ""

    # matches = re.findall(reg_total_price_value, total_price + text.description)
    # if len(matches) == 1:
    #     total_price = matches[0]
    #     target_min_different_y = abs(center_y - target_center_y)
    # elif len(matches) > 1 and abs(center_y - target_center_y) < target_min_different_y:
    #     total_price = matches[1]
    #     target_min_different_y = abs(center_y - target_center_y)
    # else:
    #     total_price = total_price

    
    # if (
    #     abs(target_min_y - min_y) < horizonal_threshold
    #     and abs(target_max_y - max_y) < horizonal_threshold
    #     and target_min_x - max_x > 0  # 合計の文字より右にある文字の場合
    # ):
    # target_center_x = (target_max_x+target_min_x)/2 
    # target_center_y = (target_max_y+target_min_y)/2
    # if(target_center_y >= min_y - horizonal_threshold and target_center_y <= max_y + horizonal_threshold
    #     and target_min_x - max_x > 0  # 合計の文字より右にある文字の場合
    # ):
 
    # document = response.full_text_annotation
    # for page in document.pages:
    #     for block in page.blocks:
    #         for paragraph in block.paragraphs:
    #             for word in paragraph.words:
    #                 for symbol in word.symbols: #左上のBBOXの情報をx,yに集約
    #                     x = symbol.bounding_box.vertices[0].x
    #                     y = symbol.bounding_box.vertices[0].y
    #                     text = symbol.text
    #                     bounds.append([x, y, text, symbol.bounding_box])