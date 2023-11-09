# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : receipt_vision.py
#  Function    : データ変換処理を行う
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     :
# ******************************************************************************/

import re
import requests
from bs4 import BeautifulSoup
import vision_doc_detect
import json
import convert_YMD
api_url = 'http://www.jpnumber.com/searchnumber.do?'

# 正規表現
number_company_list = [r"T\d{13}|登.*録.*番.*号.*\d+|事.*業.*者.*登.*録.*\d+"]
phone_match_list = [r'\d{2,5}-\d{2,4}-\d{4}|\(\d{4}\)\d{2}-\d{4}|\d{4}-\d{6}']
day_match_list = [
    r'\d{2,4}[年][^年月日]*\d{1,2}[月][^年月日]*\d{1,2}[日]|\d{2,4}/\d{2}/\d{2}']
small_price_list = [r"小.*計|お.*買.*上.*¥"]
tax_price_list = [
    r".*外.*税.*¥|.*内.*税.*¥|.*消.*費.*税.*¥|.*税.*金.*¥|.*税.*額.*¥|8%対象.*¥|10%対象.*¥"]
discount_price_list = [r".*値.*引|.*奉.*仕.*額"]
total_price_list = [r"(?<!.)合.*計"]
price_list = [r"[¥\\\\][0-9,.]+|\d{1,3}(?:[,.]\d{3})+|[0-9,.]+円|\d{1,9}"]
branch_list = [r".*店"]

receipt_keys = [
    "適格請求書発行者番号",
    "取引先",
    "取引日付",
    "件名（決済理由）",
    "番号",
    "商品名",
    "単価",
    "単位",
    "数量",
    "金額",
    "割引⾦額",
    "消費税情報",
    "⼩計金額",
    "⼩計消費税金額",
    "⼩計値引き額",
    "合計金額",
    "合計消費税金額"]

meta = {
    "angle": 0.6009566353501243,
    "estimatedLanguage": "ja",
    "imageSize": {
        "height": 598,
        "width": 312
    }
}

class ReceiptInfo:
    def __init__(self, lines) -> None:
        self.lines = lines

    def find_comapy_name(self, res, regname):
        soup = BeautifulSoup(res, 'html.parser')
        company_name = ""
        dt_element = soup.find_all('dt')
        for element in dt_element:
            if "事業者名" in element.text:
                if element.find('a', class_='result', href=lambda href: href and regname in href):
                    company_name = element.text
        return company_name.replace("事業者名：", "")

    def get_company_name(self, phonenumber):
        company_name = ""
        phonenumber = re.sub(r'[()\-]', '_', phonenumber)
        if phonenumber.count("_") == 1:
            phonenumber = phonenumber.replace("_", "")
            phonenumber = f"{phonenumber[:4]}_{phonenumber[4:7]}_{phonenumber[7:]}"    
        regname = "numberinfo_{}.html".format(phonenumber).replace("__", "_")
        params = {
            'number': phonenumber.replace("_", "")
        }
        response = requests.get(api_url, params=params, headers={
            'User-Agent': 'Chrome/117.0.0.0',
        })

        if response.status_code == 200:
            data = response.text
            company_name = self.find_comapy_name(data, regname)
        return company_name

    def find_val(self, text, reg):
        for element in reg:
            matches = re.findall(element, text)
        result = "".join(matches)
        if reg == price_list:
            if len(matches) > 1:
                result = matches[len(matches) - 1]
        return result

    def get_muti_val(self, arrVal):
        muti_val = []
        for pos in arrVal:
            val_tmp = []
            price_tmp = self.find_val(self.lines[pos], price_list)
            name_tmp = self.lines[pos].replace(price_tmp, "")
            if len(price_tmp) > 0:
                val_tmp.append(name_tmp)
                val_tmp.append(price_tmp)
                muti_val.append(val_tmp)
        return muti_val

    def get_idx_base(self, type):
        index = -1
        for idx, line in enumerate(self.lines):
            value = self.find_val(line, type)
            if len(value) > 0:
                index = idx
                break
        return index

    def get_arr_tax_base(self):
        arr_idx = []
        for idx, line in enumerate(self.lines):
            value = self.find_val(line, tax_price_list)
            if len(value) > 0:
                arr_idx.append(idx)
        return arr_idx

    def get_arr_discount_base(self):
        arr_idx = []
        for idx, line in enumerate(self.lines):
            value = self.find_val(line, discount_price_list)
            if len(value) > 0:
                arr_idx.append(idx)
        return arr_idx

    def get_total_idx(self):
        return self.get_idx_base(total_price_list)

    def get_small_idx(self):
        return self.get_idx_base(small_price_list)

    def get_first_tax_idx(self):
        return self.get_idx_base(tax_price_list)

    def get_date_idx(self):
        return self.get_idx_base(day_match_list)

    def get_number_idx(self):
        return self.get_idx_base(number_company_list)

    def get_phone_number(self):
        number_phone = ""
        index_number_phone = self.get_idx_base(phone_match_list)
        if index_number_phone > -1:
            number_phone = self.find_val(
                self.lines[index_number_phone], phone_match_list)
        return number_phone

    def get_tax_small(self):
        arr_tax_mall = []
        total_idx = self.get_total_idx()
        small_idx = self.get_small_idx()
        arr_tax = self.get_arr_tax_base()

        if small_idx > -1 and small_idx < total_idx:
            arr_tax_mall = [x for x in arr_tax if small_idx < x < total_idx]
        return arr_tax_mall

    def get_sub_total(self):
        total_price = 0
        arr_tax_total = self.get_tax_total()
        if len(arr_tax_total) > 0:
            tmpIdx = arr_tax_total[0] - 1
            while (tmpIdx > 0):
                value = self.find_val(self.lines[tmpIdx], price_list)
                if len(value) > 0:
                    total_price = value
                    break
                tmpIdx = tmpIdx - 1
        return total_price

    def get_tax_total(self):
        arr_tax_total = []
        total_idx = self.get_total_idx()
        small_idx = self.get_small_idx()
        arr_tax = self.get_arr_tax_base()

        if small_idx == -1:
            arr_tax_total = arr_tax
        else:
            arr_tax_total = [x for x in arr_tax if x > total_idx]
        return arr_tax_total

    def get_branch(self):
        return self.get_idx_base(branch_list)

    def get_item_index_loop(self):
        index_loop = []
        arrTmp = []
        first_line = -1
        end_line = -1

        first_line = self.get_date_idx() + 1
        arrTmp.append(self.get_total_idx())
        arrTmp.append(self.get_small_idx())
        arrTmp.append(self.get_first_tax_idx())
        filtered_numbers = [num for num in arrTmp if num != -1]
        if len(filtered_numbers) > 0:
            end_line = min(filtered_numbers)
        else:
            return index_loop
        index_loop.append(first_line)
        index_loop.append(end_line)
        return index_loop

    def get_partern(self, title_idx):
        val = ""
        muti_val = []

        if title_idx == 0:
            if self.get_number_idx() < 0:
                val = ""
            else:
                val = self.find_val(
                    self.lines[self.get_number_idx()], number_company_list)

        if title_idx == 1:
            val = self.get_company_name(self.get_phone_number())

        if title_idx == 2:
            if self.get_date_idx() < 0:
                val = ""
            else:
                val = self.find_val(
                    self.lines[self.get_date_idx()], day_match_list)

        if title_idx == 4:
            muti_val = self.get_item_index_loop()
            return muti_val

        if title_idx == 12:
            if self.get_small_idx() < 0:
                val = ""
            else:
                val = self.find_val(
                    self.lines[self.get_small_idx()], price_list)

        if title_idx == 13:
            muti_val = self.get_muti_val(self.get_tax_small())

        if title_idx == 14:
            muti_val = self.get_muti_val(self.get_arr_discount_base())

        if title_idx == 15:
            if self.get_total_idx() < 0:
                val = ""
            else:
                val = self.find_val(
                    self.lines[self.get_total_idx()], price_list)

        if title_idx == 16:
            muti_val = self.get_muti_val(self.get_tax_total())

        result_arr = []
        if len(muti_val) > 0:
            for e in muti_val:
                data = []
                data.append(e[0])
                data.append(e[1])
                result_arr.append(data)
        else:
            if len(val) > 0:
                result_arr.append(val)
        return result_arr

    def call_houjin_number(self, company_number):
        url = "https://api.houjin-bangou.nta.go.jp/1/num"
        params = {
            "id": "KSeJztmzMbGZA",
            "number": company_number,
            "type": "01",
            "history": "0"
        }
        company_name = ""
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.text.strip().split(',')
            if len(data) > 9:
                company_name = data[9].replace("\"", "")
        return company_name

    def getInfo(self):
        infoVal = {
        }
        # 適格請求書発行者番号
        company_number = self.get_partern(0)
        infoVal[receipt_keys[0]] = company_number
        # 取引先
        company_name = self.get_partern(1)
        if len(company_name) == 0 and len(company_number) > 0:
            company_name = self.call_houjin_number(
                re.sub(r'T', '', company_number[0]))
            branch_name = self.lines[self.get_branch()]
            if len(branch_name) > 0:
                company_name = "".join([company_name, branch_name])
        infoVal[receipt_keys[1]] = company_name
        # 取引日付
        infoVal[receipt_keys[2]] = self.get_partern(2)
        # 小計金額
        small_price = self.get_partern(12)
        infoVal[receipt_keys[12]] = small_price
        # 小計消費税金額
        tax1 = self.get_partern(13)
        infoVal[receipt_keys[13]] = tax1
        # 小計値引き額
        discount1 = self.get_partern(14)
        infoVal[receipt_keys[14]] = discount1
        # 合計金額
        total_price = self.get_partern(15)
        if len(total_price) == 0:
            total_price = "{}".format(self.get_sub_total())
        infoVal[receipt_keys[15]] = total_price
        # 合計消費税金額
        tax2 = self.get_partern(16)
        # if len(small_price) == 0 and len(tax1) > 0 and len(tax2) == 0:
        #     tax2 = tax1
        #     infoVal[receipt_keys[13]] = ""
        infoVal[receipt_keys[16]] = tax2
        # 明細情報
        infoVal["明細情報"] = self.show_detail_item()
        json_data = json.dumps(infoVal, ensure_ascii=False, indent=4)
        with open("test.json", "w", encoding="utf-8") as file:
            file.write(json_data)
        return json_data

    # ManTrinh đang xử lí
    # def conv_line_to_turtle(self, text):
    #     detailItem = {}
    #     arrItem = text.split()
    #     detailItem["name"] = ""
    #     price = self.find_val(text, price_list)
    #     detailItem["price"] = price
    #     if len(price) > 0:
    #         detailItem["name"] = text.replace(price, "").replace("円", "")
    #     return detailItem

    def test(self, text):
        detailItem = []
        arrIdx = []
        text = re.sub(r'(?<!\s)¥', " ¥", text)
        arrItem = text.split()
        for i, target in enumerate(arrItem):
            if re.search(price_list[0], target):
                arrIdx.append(i)
        startTmp = 0
        if len(arrIdx) > 1:
            for i in range(len(arrIdx) - 1):
                arrTmp = []
                start = 0
                end = 0

                if i == 0:
                    end = arrIdx[i]
                    arrTmp = arrItem[0:end+1]
                else:
                    start = startTmp
                    end = arrIdx[i]
                    arrTmp = arrItem[start:end+1]
                startTmp = end + 1
                detailItem.append(arrTmp)
        else:
            detailItem.append(arrItem)

        # ManTrinh đang xử lí
        # detailItem["name"] = ""
        # price = self.find_val(text, price_list)
        # detailItem["price"] = price
        # if len(price) > 0:
        #     detailItem["name"] = text.replace(price, "").replace("円", "")
        return detailItem

    def show_detail_item(self):
        arrVal = []
        tmp = []
        # ManTrinh đang xử lí
        # itemTmp = {}
        arr_idx_loop = self.get_partern(4)
        if len(arr_idx_loop) == 0:
            return arrVal
        for i in range(arr_idx_loop[0], arr_idx_loop[1]):
            # ManTrinh đang xử lí
            # bCheck = self.find_val(self.lines[i], price_list)
            # if len(bCheck) == 0:
            #     continue
            # itemTmp = self.conv_line_to_turtle(self.lines[i])
            # arrVal.append(itemTmp)

            tmp.append(self.lines[i])
        text = " ".join(tmp)
        self.test(text)
        return arrVal
    
    def find_houjin_number(self, resultText):
        val = ""
        if len(resultText) > 0:
            val = "".join(re.findall(r'\d+', "".join(resultText)))
            if len(val) == 13:
                val = "T{}".format(val)
        return val    

    def get_json_info(self, resultText, type):
        jsonFormat = {}
        val = ""
        # jsonFormat["boundingBoxes"] = boundingBoxes
        # jsonFormat["confidenceScore"] = confidenceScore
        if type == 0:
            # T13 Number
            val = self.find_houjin_number(resultText)
        else:
            val = "".join(resultText)    
        jsonFormat["text"] = val
        return jsonFormat
    
    def get_price_json_info(self, resultText):
        jsonFormat = {}
        jsonFormatSub = {}
        if type(resultText) is list:
            resultText = "".join(resultText)
        jsonFormatSub["value"] = "{}".format(int(re.sub(r'\D', '', resultText)))
        jsonFormat["formatted"] = jsonFormatSub
        jsonFormat["text"] = resultText
        return jsonFormat
    
    def get_date_json_info(self, resultText):
        jsonFormat = {}
        resultText = "".join(resultText)
        jsonFormat["formatted"] = convert_YMD.json_date_result(resultText)
        jsonFormat["text"] = resultText
        return jsonFormat

    def get_Service_Detect(self):
        infoVal = {}
        resultVal = {}
        storeInfoVal = {}
        totalPrice = {}
        paymentInfo = {}
        # 適格請求書発行者番号
        company_number = self.get_partern(0)
        storeInfoVal["companyId"] = self.get_json_info(company_number, 0)
        # infoVal[receipt_keys[0]] = company_number
        # 取引先
        # company_name = self.get_partern(1)
        company_name = ""
        if len(company_number) > 0:
            company_name = self.call_houjin_number(
                 re.sub(r'T', '', self.find_houjin_number(company_number)))
            branch_name = ""
            if self.get_branch() > -1:
                branch_name = self.find_val(
                    self.lines[self.get_branch()], branch_list)
            if len(branch_name) > 0:
                company_name = " ".join([company_name, branch_name])
        storeInfoVal["name"] = self.get_json_info(company_name, 1)
        # infoVal[receipt_keys[1]] = company_name
        # 取引日付
        # infoVal[receipt_keys[2]] = self.get_partern(2)
        paymentInfo["date"] = self.get_date_json_info(self.get_partern(2))
        # 小計金額
        # small_price = self.get_partern(12)
        # infoVal[receipt_keys[12]] = small_price
        # 小計消費税金額
        # tax1 = self.get_partern(13)
        # infoVal[receipt_keys[13]] = tax1
        # 小計値引き額
        # discount1 = self.get_partern(14)
        # infoVal[receipt_keys[14]] = discount1
        # 合計金額
        total_price = self.get_partern(15)
        if len(total_price) == 0:
            total_price = "{}".format(self.get_sub_total())
        totalPrice["price"] = self.get_price_json_info(total_price)
        # infoVal[receipt_keys[15]] = total_price
        # 合計消費税金額
        # tax2 = self.get_partern(16)
        # if len(small_price) == 0 and len(tax1) > 0 and len(tax2) == 0:
        #     tax2 = tax1
        #     infoVal[receipt_keys[13]] = ""
        # infoVal[receipt_keys[16]] = tax2
        # 明細情報
        # infoVal["明細情報"] = self.show_detail_item()
        resultVal["storeInfo"] = storeInfoVal
        resultVal["totalPrice"] = totalPrice
        resultVal["paymentInfo"] = paymentInfo
        
        infoVal["meta"] = meta
        infoVal["result"] = resultVal
        json_data = json.dumps(infoVal, ensure_ascii=False, indent=4)

        return json_data


def getResult(file_byte_data):
    content = vision_doc_detect.detect_text(file_byte_data)
    all_text = [item[0] for item in content]
    obj = ReceiptInfo(all_text)
    return obj.getInfo()


def getAPI(file_byte_data):
    content = vision_doc_detect.detect_text(file_byte_data)
    all_text = [item[0] for item in content]
    obj = ReceiptInfo(all_text)
    return obj.get_Service_Detect()
