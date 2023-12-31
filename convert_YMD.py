# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : convert_YMD.py
#  Function    : 年月日を変換する
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/

import unicodedata
import re
import datetime

# 各年号の元年を定義
eraDict = {
    "明治": ["M",1868,908,45],
    "大正": ["T",1912,712,15],
    "昭和": ["S",1926,1225,64],
    "平成": ["H",1989,108,31],
    "令和": ["R",2019,501],
}

# formatted = {}

def get_gengo_year(year,md):
    gengo = ""
    reversed_era_items = reversed(list(eraDict.items()))
    for era, era_data in reversed_era_items:
        tmp_val = (era_data[1] * 10000 + era_data[2])
        if year <= era_data[3]:
            ymd_val = (era_data[1] + year - 1) * 10000 + md
            if ymd_val >= tmp_val: 
                gengo = era
                break
    return gengo        

def japanese_calendar_converter(text):
    year_ = 0
    month_ = int(re.sub(r'\D', '', text.split("年")[1].split("月")[0]))
    day_ = int(re.sub(r'\D', '', text.split("月")[1].split("日")[0]))
    md_val = month_*100 + day_
    str_tmp = text.split("年")[0]
    # Tách năm, tháng và ngày từ chuỗi
    if len(str_tmp) == 3:
        str_tmp = text.split("年")[0][1:]
    if len(str_tmp) > 0 and len(str_tmp) < 3:
        # Lấy năm hiện tại
        current_year = datetime.datetime.now().year
        compare_year = int("{}".format(current_year)[-2:])
        year_ = int(str_tmp)
        for era, era_data in eraDict.items():
            if era == "令和":
                era_data.append(current_year-era_data[1]+1)
        if year_ <= compare_year and year_ > eraDict["令和"][3]:
            return datetime.date(2000 + year_, month_, day_)
        else:
            text = "{}{}".format(get_gengo_year(year_, md_val),text)
        
    # 正規化
    normalized_text = unicodedata.normalize("NFKC", text)

    # 年月日を抽出
    pattern = r"(?P<era>{eraList})(?P<year>[0-9]{{1,2}}|元)年(?P<month>[0-9]{{1,2}})月(?P<day>[0-9]{{1,2}})日".format(eraList="|".join(eraDict.keys()))
    date = re.search(pattern, normalized_text)

    # 抽出できなかったら終わり
    if date is None:
        print("Cannot convert to western year")

    # 年を変換
    for era, startYear in eraDict.items():
        if date.group("era") == era:
            if date.group("year") == "元":
                year = eraDict[era]
            else:
                year = eraDict[era][1] + int(date.group("year")) - 1
    
    # date型に変換して返す
    return datetime.date(year, int(date.group("month")), int(date.group("day")))

def conv_str_to_date(text):
    # Sử dụng hàm strptime để chuyển chuỗi ngày tháng thành đối tượng datetime
    year_ = int(re.sub(r'\D', '', text.split("年")[0].split("年")[0]))
    month_ = int(re.sub(r'\D', '', text.split("年")[1].split("月")[0]))
    day_ = int(re.sub(r'\D', '', text.split("月")[1].split("日")[0]))
    return datetime.date(year_, month_, day_)

def conv_gengo_char(allVal):
    gengo_year = 0
    bFlag = False
    val = allVal[0]
    
    count_year = int("".join(re.findall(r'\d', val)))
    for era, era_data in eraDict.items():
        if era_data[0] in val:
            gengo_year = era_data[1] + count_year - 1
            bFlag = True
            break
    if bFlag == False and count_year < 100:
        #From 2000
        text = "{}年{}月{}日".format(count_year, allVal[1], allVal[2])
        date_val = japanese_calendar_converter(text)
        gengo_year = date_val.year
    return gengo_year

def get_only_digits(value):
    return ''.join(x for x in value if x.isdigit())

def json_date_result(text):
    formatted = {}
    if len(text) == 0:
        return formatted
    if re.search(r'[年月日]', text):
        ortherCharacter = re.compile(r'[^年月日0-9]')
        text = re.sub(ortherCharacter, '', text)
        year_val = text.split("年")[0].split("年")[0]
        if re.match(r'^\d{4}$', year_val):
            date_val = conv_str_to_date(text)
        else:
            date_val = japanese_calendar_converter(text)
        if date_val is not None:
            y_ = int(date_val.year)
            m_ = int(date_val.month)
            d_ = int(date_val.day)

            #Set tạm
            if y_ == 2013:
                y_ = 2023

            formatted["day"] = "{}".format(f"{d_:02}")      
            formatted["month"] = "{}".format(f"{m_:02}")  
            formatted["year"] = "{}".format(y_)    
    else:
        arr_format = []
        arr_format = text.replace('/', ' ').replace('-', ' ').split()
        gengo_year = ""
        if len(arr_format) > 0:
            gengo_year = conv_gengo_char(arr_format)
            if gengo_year > 0:
                arr_format[0] = "{}".format(gengo_year)

            # formatted["day"] = "{}".format(f"{arr_format[2]:02}")      
            # formatted["month"] = "{}".format(f"{arr_format[1]:02}")  
            # formatted["year"] = "{}".format(arr_format[0])
            y_ = int(get_only_digits(arr_format[0]))
            m_ = int(get_only_digits(arr_format[1]))
            d_ = int(get_only_digits(arr_format[2]))

            #Set tạm
            if y_ == 2013:
                y_ = 2023

            formatted["day"] = "{}".format(f"{d_:02}")      
            formatted["month"] = "{}".format(f"{m_:02}")  
            formatted["year"] = "{}".format(y_) 

    return formatted
