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
    "明治": [1868,908,45],
    "大正": [1912,712,15],
    "昭和": [1926,1225,64],
    "平成": [1989,108,31],
    "令和": [2019,501],
}

formatted = {}

def get_gengo_year(year,md):
    gengo = ""
    reversed_era_items = reversed(list(eraDict.items()))
    for era, era_data in reversed_era_items:
        tmp_val = (era_data[0] * 10000 + era_data[1])
        if year <= era_data[2]:
            ymd_val = (era_data[0] + year - 1) * 10000 + md
            if ymd_val >= tmp_val: 
                gengo = era
                break
    return gengo        

def japanese_calendar_converter(text):
    year_ = 0
    month_ = int(text.split("年")[1].split("月")[0])
    day_ = int(text.split("月")[1].split("日")[0])
    md_val = month_*100 + day_
    # Tách năm, tháng và ngày từ chuỗi
    if len(text.split("年")[0]) == 2:
        # Lấy năm hiện tại
        current_year = datetime.datetime.now().year
        year_ = int(text.split("年")[0])
        for era, era_data in eraDict.items():
            if era == "令和":
                era_data.append(current_year-era_data[0]+1)
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
                year = eraDict[era][0] + int(date.group("year")) - 1
    
    # date型に変換して返す
    return datetime.date(year, int(date.group("month")), int(date.group("day")))

def conv_str_to_date(text):
    # Sử dụng hàm strptime để chuyển chuỗi ngày tháng thành đối tượng datetime
    year_ = int(text.split("年")[0].split("年")[0]) 
    month_ = int(text.split("年")[1].split("月")[0])
    day_ = int(text.split("月")[1].split("日")[0])
    return datetime.date(year_, month_, day_)


def json_date_result(text):
    if len(text) == 0:
        return formatted
    year_val = text.split("年")[0].split("年")[0]
    if re.match(r'^\d{4}$', year_val):
        date_val = conv_str_to_date(text)
    else:
        date_val = japanese_calendar_converter(text)
    if date_val is not None:
        formatted["day"] = "{}".format(f"{date_val.day:02}")      
        formatted["month"] = "{}".format(f"{date_val.month:02}")  
        formatted["year"] = "{}".format(date_val.year)    
    return formatted    

