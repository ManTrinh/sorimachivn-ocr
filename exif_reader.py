from PIL import Image
from PIL.ExifTags import TAGS
import io

import glob
class Exif():

    # クラス変数
    '''
    オリエン手＝ションの文字列
    CWはClock Wiseの略
    '''
    OrientationStringList = [
        'Undefined',
        'Horizontal (normal)',
        'Mirror horizontal',
        'Rotate 180',
        'Mirror vertical',
        'Mirror horizontal and rotate 270 CW',
        'Rotate 90 CW',
        'Mirror horizontal and rotate 90 CW',
        'Rotate 270 CW'
    ]
    '''
    1	そのまま
    2	上下反転(上下鏡像?)
    3	180度回転
    4	左右反転
    5	上下反転、時計周りに270度回転
    6	時計周りに90度回転
    7	上下反転、時計周りに90度回転
    8	時計周りに270度回転
    '''

    def __init__(self):
        self.exif_dict = {}
        self.origin_size = {}

    def read(self, byte_data):
        '''
        JPEGのEXIFを取り出す
        :param jpeg_full_path: JPEGファイルのフルパス
        :return:
        '''

        self.exif_dict = {}
        img_io = io.BytesIO(byte_data)
        im = Image.open(img_io)
        self.origin_size['width'] = im.width
        self.origin_size['height'] = im.height
        # Exif データを取得
        # 存在しなければそのまま終了 空の辞書を設定
        try:
            exif = im._getexif()
            # タグIDそのままでは人が読めないのでデコードして
            # テーブルに格納する
            self.exif_dict = {}
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                self.exif_dict[tag] = value
        except AttributeError:
            return

    def get_origin_size(self):
        return self.origin_size

    def get_Orientation(self):
        '''
        JPEGの向きを取り出す。（存在しない場合は0を返す)
        :return: Orienattion の数値
        '''
        return self.exif_dict.get('Orientation', 0)

    def get_Exif_image_width(self):
        '''
        JPEGのExifImageWidth。（存在しない場合は0を返す)
        :return: ExifImageWidth の数値
        '''
        return self.exif_dict.get('ExifImageWidth', 0)

    def get_Exif_image_height(self):
        '''
        ExifImageHeight。（存在しない場合は0を返す)
        :return: ExifImageWidth の数値
        '''
        return self.exif_dict.get('ExifImageHeight', 0)

    def get_value_by_key(self, key):
        '''
        指定されたkeyの値を返す。（存在しない場合はNoneを返す
        :param key: 取得したいkey
        :return: keyに対応する値
        '''
        return self.exif_dict.get(key, None)



def read_all_info_under_dir():
    Path = "/Users/benzakimuneyoshi/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi/Data/20181218_Data/sorimachi_img_20181225/*.jpg"

    files = glob.glob(Path)
    exif = Exif()
    for file in files:
        exif.read(file)
        message = '{}: width:{}, height:{}, file={}'.format(
            exif.get_Orientation(),
            exif.get_Exif_image_width(),
            exif.get_Exif_image_height(),
            file
        )
        print(message)

    pass

def check_typical_data():
    File = "/Users/benzakimuneyoshi/Dropbox/Software Tech/AnacondaProjects/13 Sorimachi/Data/20181218_Data/sorimachi_img_20181225/sori_20181220 (1000).jpg"
    exif = Exif()
    exif.read(File)

    print('File = ' + File)
    print('\tExifImageWidth ', exif.get_Exif_image_width())
    print('\tExifImageHeight ', exif.get_Exif_image_height())
    orientation = exif.get_Orientation()

    print('\tOrientation num:{} ({})'.format(
        orientation, Exif.OrientationStringList[orientation]) )
    if orientation != 6:
        print('+++++++++++++++++++++++++++++++++++++++++++++')


if __name__ == '__main__':
    check_typical_data()
    print('----------------------------')
    read_all_info_under_dir()

    pass

