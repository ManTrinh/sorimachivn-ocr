import json
import os
import base64
import requests
import time
import re
from PIL import Image

from exif_reader import Exif
from io import BytesIO

import math
import numpy as np

from translation import Affine


class GoogleTextDetection():

    def __init__(self, config_file='./config/config.json'):

        # exif後の方向
        self.orientation = Affine.UnKnown

        # Jsonのトップの辞書
        self.top_dict = {}

        # FullTextAnnotationの結果
        self.parse_string_list = []
        self.parse_bounding_boxes = []

        # TextAnnotationのトップ

        self.image = None
        self.exif_orientation = 0
        self.width = 0
        self.height = 0

        # レシートの傾き
        self.gradient = None

        # 縦方向の文字列
        self.vertical_lines = []

        self.config_file = config_file
        self.config = {}
        # コンフィグファイルの読み込み
        with open(self.config_file, encoding='utf-8-sig') as f:
            try:
                self.config = json.load(f)
            except json.JSONDecodeError as e:
                print('[td]'+e.msg, e)

    def __parse_symbol__(self, symbol):
        text = symbol.get('text')
        self.parse_string_list.append(text)
        bounding_box = symbol.get('boundingBox')

        xmin = 100000
        ymin = 100000
        xmax = -1
        ymax = -1
        vertices = bounding_box['vertices']
        for vertex in vertices:
            x = vertex.get('x', 0)
            y = vertex.get('y', 0)
            if x < 0:
                x = 0
            if y < 0:
                y = 0

            if x < xmin:
                xmin = x
            if x > xmax:
                xmax = x
            if y < ymin:
                ymin = y
            if y > ymax:
                ymax = y

        self.parse_bounding_boxes.append(
            {'text': text, 'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax})

    def __update_symbol__(self, symbol, matrix):
        text = symbol.get('text')
        self.parse_string_list.append(text)
        bounding_box = symbol.get('boundingBox')

        vertices = bounding_box['vertices']
        rects = []
        for vertex in vertices:
            x = vertex.get('x', 0)
            y = vertex.get('y', 0)
            rects.append([x, y, 1])

        trans = Affine.translate(matrix, rects)

        for index, vertex in enumerate(vertices):
            vertex['x'] = trans[index, 0]
            vertex['y'] = trans[index, 1]

    def __parse_word__(self, word, matrix):
        symbols = word.get('symbols')
        for symbol in symbols:
            if matrix is None:
                self.__parse_symbol__(symbol)
            else:
                self.__update_symbol__(symbol, matrix)
        pass

    def __parse_paragraph__(self, paragrah, matrix):

        words = paragrah.get('words')
        for word in words:
            self.__parse_word__(word, matrix)
        pass

    def __parse_block__(self, block, matrix=None):

        paragraphs = block['paragraphs']

        for paragraph in paragraphs:
            self.__parse_paragraph__(paragraph, matrix)

        pass

    def __get_orientation__(self):
        '''
        Googleのテキストアノテーションから方向を取得する
        :return: Affine.CW0, Affine.CW90, Affine.CW180. Affine.CW270, Affine.Unkwnonのいずれか
        '''

        # 0からGoogleTextDetection.ORIENTATION_UNKNOWNまでのリストを作成し、0にする。
        orientations_count = [0] * (Affine.UnKnown+1)

        # テキストアノテーションを取得する
        text_annotations = self.get_textAnnotations()
        first = True
        # KHANH 2019/03/26 支払値段縦方向検索の対応　追加　↓
        payPrice = ""
        # KHANH 2019/03/26 支払値段縦方向検索の対応　追加　↑
        for text_annotation in text_annotations:
            if first:   # 1行目には全文が入っているので、無視する
                first = False
                continue

            bounding_poly = text_annotation.get('boundingPoly')
            if bounding_poly is None:
                return Affine.UnKnown

            vertices = bounding_poly['vertices']
            if vertices is None or (len(vertices) != 4):  # 矩形でない場合はチェックしない
                orientations_count[Affine.UnKnown] += 1
                continue

            x1 = vertices[0].get('x')
            x2 = vertices[1].get('x')
            x3 = vertices[2].get('x')
            x4 = vertices[3].get('x')
            if (not x1) or (not x2) or (not x3) or (not x4):
                message = 'check_orientation x is none {}, {}, {}, {}'.format(
                    x1, x2, x3, x4)
                orientations_count[Affine.UnKnown] += 1
                continue

            # KHANH 2019/03/26 支払値段縦方向検索の対応　追加　↓
            # 支払値段が検索したい文字列の下にある場合
            description = text_annotation.get('description')
            below_strings = ['当月御請求額', '御請求金額', '今回請求金額', '当月お買上額', '当月ご請求額', '今回御請求額', '当月請求金額', '御請求額', '当月請求合計額',
                             'ご請求額', '当月請求額', '今回御請求金額', '今回ご請求額', '当月請求額合計', '今回ご請求高', '訂正後領取額', '訂正後領収額', '合計金額', '全期分']
            for below_string in below_strings:
                if below_string == description:
                    x_min = vertices[0].get('x')
                    x_max = vertices[1].get('x')
                    y_max = vertices[2].get('y')
                    with open(self.json_file, 'r', encoding="utf-8", errors='ignore') as file:
                        jsonDictData = json.load(file)
                        price_list = []
                        find_y_min_list = []
                        for jsonDict_keys in jsonDictData['responses']:
                            for json_key in jsonDict_keys['textAnnotations']:
                                findbox = json_key['boundingPoly']['vertices']
                                point1 = findbox[0]
                                payPrice_xMin = point1.get('x')
                                payPrice_yMin = point1.get('y')
                                if x_min < payPrice_xMin and payPrice_xMin < x_max and payPrice_yMin > y_max:
                                    find_yMin = point1.get('y')
                                    find_y_min_list.append(find_yMin)
                                    if payPrice_yMin < min(find_y_min_list) + 10:
                                        price_list.append(
                                            json_key['description'])
                        priceStr = "".join(price_list)
                        payPrice = ''.join(re.findall('\d+', priceStr))
                    file.close()
            # 支払値段が検索したい文字列の右下にある場合
            if description == "納入金額" or description == "納入金額(" or description == "納入金額(1" or description == "納入金額(1)":
                x_min = vertices[0].get('x')
                x_max = vertices[1].get('x')
                y_max = vertices[2].get('y')
                with open(self.json_file, 'r', encoding="utf-8", errors='ignore') as file:
                    jsonDictData = json.load(file)
                    price_list = []
                    find_y_min_list = []
                    for jsonDict_keys in jsonDictData['responses']:
                        for json_key in jsonDict_keys['textAnnotations']:
                            findbox = json_key['boundingPoly']['vertices']
                            point1 = findbox[0]
                            payPrice_xMin = point1.get('x')
                            payPrice_yMin = point1.get('y')
                            if x_min < payPrice_xMin and payPrice_xMin < x_max + 250 and payPrice_yMin > y_max:
                                find_yMin = point1.get('y')
                                find_y_min_list.append(find_yMin)
                                if payPrice_yMin < min(find_y_min_list) + 10:
                                    price_list.append(json_key['description'])
                    priceStr = "".join(price_list)
                    payPrice = ''.join(re.findall('\d+', priceStr))
                    if description != "":
                        break
                file.close()
            # KHANH 2019/03/26 支払値段縦方向検索の対応　追加　↑

            y1 = vertices[0].get('y')
            y2 = vertices[1].get('y')
            y3 = vertices[2].get('y')
            y4 = vertices[3].get('y')
            if (not y1) or (not y2) or (not y3) or (not y4):
                message = 'check_orientation y is none {}, {}, {}, {}'.format(
                    y1, y2, y3, y4)
                orientations_count[Affine.UnKnown] += 1
                continue

            deg1 = np.rad2deg(np.arctan2(y2 - y1, x2 - x1))
            deg3 = np.rad2deg(np.arctan2(y3 - y4, x3 - x4))

            # marginは5度にしておく
            margin = 6
            if (-margin < deg1) and (deg1 < margin) and (-margin < deg3) and (deg3 < margin):
                orientations_count[Affine.CW0] += 1
            elif ((180 - margin) < abs(deg1)) and ((abs(deg1)) < (180 + margin)) and ((180 - margin) < abs(deg3)) and (
                    abs(deg3) < (180 + margin)):
                orientations_count[Affine.CW180] += 1
            elif ((90 - margin) < deg1) and (deg1 < (90 + margin)) and ((90 - margin) < deg3) and (
                    deg3 < (90 + margin)):
                orientations_count[Affine.CW90] += 1
            elif ((-90 - margin) < deg1) and (deg1 < (-90 + margin)) and ((-90 - margin) < deg3) and (
                    deg3 < (-90 + margin)):
                orientations_count[Affine.CW270] += 1
            else:
                orientations_count[Affine.UnKnown] += 1

        # orientations_countの最も大きいものを方向にする
        orientation = np.argmax(orientations_count)

        # 同じ方向かどうかをチェック
        print_flag = False
        for i in range(len(orientations_count)):
            if (i != orientation) and orientations_count[i] != 0:
                print_flag = True

        self.orientation = orientation
        # KHANH 2019/03/26 支払値段縦方向検索の対応　追加　↓
        # return orientation
        return orientation, payPrice
        # KHANH 2019/03/26 支払値段縦方向検索の対応　追加　↑

    def __parse_fullTextAnnotation__(self):

        try:
            self.parse_string = ''
            self.parse_bounding_boxes = []
            self.parse_string_list.clear()

            fullTextAnnotation = self.top_dict["responses"][0]["fullTextAnnotation"]
            pages = fullTextAnnotation['pages']
            text = fullTextAnnotation['text']
            self.text = text

            if len(pages) > 1:
                message = 'GoogleTextDetection support only 1 page but pages is {}, detect first page only'.format(
                    len(pages))
            elif len(pages) < 1:
                message = 'GoogleTextDetection support only 1 page but pages is '.format(
                    len(pages))
                return False

            page = pages[0]

            blocks = page['blocks']

            for block in blocks:
                self.__parse_block__(block)

            self.parse_string = ''.join(self.parse_string_list)

            # 不要な、文字列のリストを削除する
            self.parse_string_list.clear()

            string_length = len(self.parse_string)
            list_length = len(self.parse_bounding_boxes)
            if string_length != list_length:
                return False

            return True
        except:
            return False

    def get_textAnnotations(self):
        return self.top_dict["responses"][0]["textAnnotations"]

    def get_textAnnotation(self):
        textAnnotations = self.get_textAnnotations()
        return textAnnotations[0]['description']

    def get_parse_string(self):
        return self.parse_string

    def get_parse_bounding_boxes(self):
        return self.parse_bounding_boxes

    def get_vertical_lines(self):
        return self.vertical_lines

    def get_gradient(self):
        if self.gradient is None:
            return self.__parse_gradient__()
        return self.gradient

    def __read_json__(self):

        # JSONファイルの読み込み
        with open(self.json_file, encoding='utf-8-sig') as f:

            try:
                self.top_dict = json.load(f)
            except json.decoder.JSONDecodeError as e:
                return False
            except ValueError as e:
                return False
            except Exception as e:
                return False

        return True

    def __detect_text__(self, retry):
        '''
        Googleからテキストデテクトを行う、（リトライ付き)
        :param image_full_path: イメージのフルパス
        :param json_full_path: 保存用JSonのフルパス
        :param retry: リトライの数
        :return:
        '''

        retry_count = 1
        while True:
            try:
                self.top_dict = self.__detect_text_internal__()
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump(self.top_dict, f, indent=2, ensure_ascii=False)
                return
            except ValueError:
                # TypeErrorはファイルサイズが大きのでリトライを行ってもしょうがないためそのまま上げる
                raise
            except:
                message = 'failed to text Google detection retry:{} image file:{}'.format(
                    retry_count, self.image_file)
                if retry_count >= retry:
                    message = 'failed to Google detection over {} image:{} json_file:{}'.\
                        format(retry, self.image_file, self.json_file)
                    raise
                retry_count += 1
                time.sleep(0.5)  # リトライ前に、0.5秒待って再度トライ

        pass

    def __load_image__(self):
        # Exifをチェックする
        exif = Exif()
        exif.read(self.image_file)

        # EXifからオリエンテーションを取得する
        self.exif_orientation = exif.get_Orientation()
        message = '{} exif exif_orientation is num:{} string:{}'.format(
            self.image_file, self.exif_orientation, Exif.OrientationStringList[
                self.exif_orientation]
        )

        self.image = Image.open(self.image_file)
        (self.width, self.height) = self.image.size
        # print('Original width', self.width, 'Original Height', self.height)

        if self.exif_orientation == 0:
            pass
        elif self.exif_orientation == 1:
            pass
        elif self.exif_orientation == 3:
            self.image = self.image.transpose(Image.ROTATE_180)
        elif self.exif_orientation == 6:  # Rotate 90 CW
            self.image = self.image.transpose(Image.ROTATE_270)
            # im = im.rotate(270, expand=True)
        elif self.exif_orientation == 8:  # Rotate 270 CW
            self.image = self.image.transpose(Image.ROTATE_90)
        else:
            message = 'no Support format: File:{}, Orientation:{}, {}'.format(
                self.image_file, self.exif_orientation, Exif.OrientationStringList[self.exif_orientation])

        (self.width, self.height) = self.image.size
        # print('New width', self.width, 'New Height', self.height)

    def __detect_text_internal__(self):
        '''
        Googleの文字列検索を行う
        :param image_full_path: jpeg/pngなどのフルパス
        :return: jsonのtop辞書
        '''

        api_url = self.config['google_text_detection_api_url'] + \
            '?key={}'.format(self.config['google_api_key'])

        buff = BytesIO()
        self.image.save(buff, format="JPEG")
        ctxt = base64.b64encode(buff.getvalue())

        # ctxt = base64.b64encode(f.read())
        req_body = json.dumps(
            {'requests': [{'image': {'content': ctxt.decode('utf-8')  # base64でエンコードしたものjsonにするためdecodeする
                                     }, 'features': [{'type': 'DOCUMENT_TEXT_DETECTION'}]}]})

        res = requests.post(api_url, data=req_body)
        if res.status_code == 200:
            return res.json()

        elif res.status_code == 400:  # ファイルが大きすぎて、googleが処理できない場合
            message = 'Googlle Text Detection fails reason = {}'.format(
                res.text.replace('\n', ' '))
            if res.text.find('Request payload size exceeds the limit') != 1:
                raise ValueError('Request payload size exceeds the limit')
            else:
                raise Exception('Google Text Detection fails')

        else:
            message = 'Googlle Text Detection fails reason = {}'.format(
                res.text.replace('\n', ' '))
            raise Exception('Google Text Detection fails')

    # レシートの傾きを求める

    def __parse_gradient__(self):
        get_textAnnotations = self.get_textAnnotations()
        if (len(get_textAnnotations) < 1):
            return 0

        gradients = []
        for annotation in get_textAnnotations:
            boxies = annotation['boundingPoly']['vertices']
            if len(boxies) < 2:
                continue
            if 'x' not in boxies[0] \
                    or 'y' not in boxies[0] \
                    or 'x' not in boxies[1] \
                    or 'y' not in boxies[1]:
                continue
            x1, y1 = int(boxies[0]['x']), int(boxies[0]['y'])
            x2, y2 = int(boxies[1]['x']), int(boxies[1]['y'])

            # 縦長のバウンディングボックスは無視
            if abs(y2-y1) > abs(x2-x1):
                continue

            gradient = math.atan2(y2-y1, x2-x1)
            gradients.append(gradient)
        gradients.pop(0)
        if len(gradients) == 0:
            return 0

        result = np.average(gradients)
        self.gradient = result
        return result

    # 行リストを作成＝＞　②一個のボックス座標をすべてx方向でソートする
    def __make_vline_list__(self):
        gradient = self.__parse_gradient__()
        target = (self.parse_bounding_boxes[0]['xmax'], self.parse_bounding_boxes[0]['ymax'],
                  self.parse_bounding_boxes[0]['xmin'], self.parse_bounding_boxes[0]['ymin'])

        vertical_lines = []
        vertical_line = []
        for bounding_box in self.parse_bounding_boxes:
            item_center_y = (bounding_box['ymin'] + bounding_box['ymax']) / 2
            item_center_x = (bounding_box['xmin'] + bounding_box['xmax']) / 2
            if not self.__is_same_line__(gradient, target, item_center_x, item_center_y):
                target = (bounding_box['xmax'], bounding_box['ymax'],
                          bounding_box['xmin'], bounding_box['ymin'])
                vertical_lines.append(vertical_line)
                vertical_line = []

            vertical_line.append(bounding_box)

        vertical_lines.append(vertical_line)
        return vertical_lines

    # 同じ行か判定 計算式：y - y1 = m(x - x1)＝＞ソートしたx方向で同じ行かを判断し、
    def __is_same_line__(self, gradient, bounding_box, terget_center_x, tartget_center_y):
        # 事前に調べた傾き(gradient)を使って(xmin,ymin)から1本、(xmax,ymax)から1本直線を引き、
        # 調べたいバウンディングボックスの中点(terget_center_x,tartget_center_y)が2本の線の間にあれば同じ行とする
        (xmax, ymax, xmin, ymin) = bounding_box
        result = tartget_center_y < gradient * \
            (terget_center_x-xmax)+ymax and gradient * \
            (terget_center_x-xmin)+ymin < tartget_center_y
        return result

    def __parse_vertical_lines__(self):

        # vertical linesをクリアする
        self.vertical_lines.clear()
        # parse_boudingg_box をY軸（縦軸方向）でソートする(ymin+ymax
        self.parse_bounding_boxes.sort(
            key=lambda item: (item['ymin'] + item['ymax']) / 2)

        # 行リストを作成
        vertical_lines = self.__make_vline_list__()

        # すべてのverticallineをx方向でソートする。
        # ついでにあとで検索しやすいようにテキストのみ取り出す
        for vertical_line in vertical_lines:
            vertical_text_list = []
            vertical_line.sort(key=lambda item: (item['xmin']))
            for bounding_box in vertical_line:
                vertical_text_list.append(bounding_box['text'])
            self.vertical_lines.append(
                {'text': ''.join(vertical_text_list), 'rects': vertical_line})

        self.dump_vertical_lines()
        pass

    def dump_vertical_lines(self):
        gradient = self.__parse_gradient__()
        for i, line in enumerate(self.vertical_lines):
            message = 'No:{}, Item<{}>'.format(i, line['text'])
            rects = line['rects']

    def check_total_existed(self):
        regex = r"合[ ]{0,}計"
        existed = False
        for line in self.vertical_lines:
            matches = re.match(regex, line['text'])
            if matches is not None:
                existed = True
                break

        return existed

    def __update_text_annotation_rectangles__(self, matrix):
        '''
        Google のtext_annotation以下の検索結果の座標を行列に従い、変換する
        :param mat: 変換する行列
        :return: なし
        '''

        textAnnotations = self.get_textAnnotations()
        for textAnnotation in textAnnotations:
            boundingPoly = textAnnotation['boundingPoly']
            vertices = boundingPoly['vertices']
            rects = []
            for vertex in vertices:
                x = vertex.get('x', 0)
                y = vertex.get('y', 0)
                rects.append([x, y, 1.])
            trans = Affine.translate(matrix, rects)

            for index, vertex in enumerate(vertices):
                vertex['x'] = trans[index, 0]
                vertex['y'] = trans[index, 1]
        pass

    def __update_full_text_annotation_rectangles__(self, matrix):
        '''
        Google のfull_text_annotation以下の検索結果の座標を行列に従い、変換する
        :param mat: 変換する行列
        :param mat: 変換する一番上の辞書
        :return: なし
        '''
        fullTextAnnotation = self.top_dict["responses"][0]["fullTextAnnotation"]
        pages = fullTextAnnotation['pages']

        if len(pages) > 1:
            message = 'GoogleTextDetection support only 1 page but pages is {}, detect first page only'.format(
                len(pages))
        elif len(pages) < 1:
            message = 'GoogleTextDetection support only 1 page but pages is '.format(
                len(pages))
            return False

        page = pages[0]

        blocks = page['blocks']

        for block in blocks:
            self.__parse_block__(block, matrix)

    def __update_rectangles__(self, matrix):
        '''
        Google の検索結果の座標を行列に従い、変換する
        :param mat: 変換する行列
        :return: なし
        '''

        # fullTextAnnotation以下の座用変換を行う
        self.__update_full_text_annotation_rectangles__(matrix)

        # fullAnnotation以下の座用変換を行う
        self.__update_text_annotation_rectangles__(matrix)

    def setup(self, image_full_path, json_full_path, force=False, retry=3):
        '''
        Googleのテキスト検出を行う。json_full_pathがあれがここから読み込む。
        ない場合は、　Googleにテキスト・ディテクションを行い、json_full_pathにjsonを保存する。
        :param jpeg_full_path:  読み込むimageファイルのfull pah
        :param json_full_path:  読み込み、書き込むJsonのキャッシュのfull pah
        :param force: Trueの場合は、jsonのキャッシュがあっても強制的にGoogleか情報を取得する
        :return: なし
        '''

        self.image_file = image_full_path
        self.json_file = json_full_path

        func_message = 'GooglTextDetection::set up Image={}, Json={}, force={}, retry={}'.format(
            self.image_file, self.json_file, force, retry
        )

        # 画像ファイルを読み、高さと幅を知る。
        self.__load_image__()

        if force:
            self.__detect_text__(retry)
        elif os.path.exists(json_full_path):
            # もしJSONの横込みに失敗した場合は、再度Googleテキスト検索を行う
            if self.__read_json__() == False:
                self.__detect_text__(retry)
        else:
            self.__detect_text__(retry)

        # TextAnnotationから方向を取得
        orientation = self.__get_orientation__()
        if orientation == Affine.CW0:
            pass
            # 何もしない
        elif orientation == Affine.CW90:
            self.__update_rectangles__(Affine.make_matrix(
                Affine.CW90, self.width, self.height))

        elif orientation == Affine.CW180:
            self.__update_rectangles__(Affine.make_matrix(
                Affine.CW180, self.width, self.height))

        elif orientation == Affine.CW270:
            self.__update_rectangles__(Affine.make_matrix(
                Affine.CW270, self.width, self.height))

        # Full TetxtAnnotationから、text
        res = self.__parse_fullTextAnnotation__()

        # fullTextAnnotationをパースして、行ごとのラインにする
        if res:
            self.__parse_vertical_lines__()


'''
ここから下はテスト用の関数
'''


def printAllText(image_parent_dir):

    detection = GoogleTextDetection()

    import glob
    glob_image_file_name = image_parent_dir + '/*.jpg'
    image_files = glob.glob(glob_image_file_name)

    count = 0
    num_of_files = len(image_files)
    for image_file in image_files:
        count += 1
        directory, file = os.path.split(image_file)
        base, ext = os.path.splitext(file)
        json_file = os.path.join(directory, base + '.json')

        print(count, '/', num_of_files)
        detection.setup(image_file, json_file)
        text = detection.get_text()
        f = open("myfile.txt", "w")
        f.write(text)
        f.close()

        message = 'base:{}, text:{}'.format(base, text)


def printTotal(image_parent_dir):

    detection = GoogleTextDetection()

    import glob
    import re

    glob_image_file_name = image_parent_dir + '/*.jpg'
    image_files = glob.glob(glob_image_file_name)

    count = 0
    num_of_files = len(image_files)

    reg_list = []

    total_regular_list = [' ?合.*計']
    total_regex = []
    for total_reg in total_regular_list:
        reg = re.compile(total_reg)
        total_regex.append(reg)

    for image_file in image_files:
        count += 1
        directory, file = os.path.split(image_file)
        base, ext = os.path.splitext(file)
        json_file = os.path.join(directory, 'cache', base + '.json')

        print(count, '/', num_of_files)
        detection.setup(image_file, json_file)
        texts = detection.get_text()
        text_list = texts.split()
        for text in text_list:
            for regex in total_regex:
                match = regex.search(text)
                if match:
                    candidate = match.group(0)
                    break


# if __name__ == '__main__':

#     if os.name == 'nt':  # Windows
#         Image_File = "D:/Benzaki/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi\Data/20181218_Data\sorimachi_img_20181225/sori_20181220 (10).jpg"
#         JSON_File = "D:/Benzaki/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi\Data/20181218_Data/sorimachi_img_20181225/cache/sori_20181220 (10).json"
#         Image_Dir = "D:/Benzaki/Dropbox/Software Tech\AnacondaProjects/13 Sorimachi\Data/20181218_Data/sorimachi_img_20181225"
#     else:
#         Image_File = "/Users/benzakimuneyoshi/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi/Data/20181218_Data/sorimachi_img_20181225/sori_20181220 (1000).jpg"
#         JSON_File = "/Users/benzakimuneyoshi/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi/Data/20181218_Data/sorimachi_img_20181225/cache/sori_20181220 (1000).json"
#         Image_Dir = "/Users/benzakimuneyoshi/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi/Data/20181218_Data/sorimachi_img_20181225"

#     # コンフィグファイルの読み込み
#     detection = GoogleTextDetection()
#     detection.setup(Image_File, JSON_File, force=True)
#     # detection.setup(Image_File, JSON_File)

#     # printAllText(Image_Dir)
#     # printTotal(Image_Dir)
