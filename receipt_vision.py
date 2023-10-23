import re
import requests
from bs4 import BeautifulSoup
import vision_doc_detect
import json
api_url = 'http://www.jpnumber.com/searchnumber.do?'

# Reg
number_company_list = [r"T\d{13}"]
phone_match_list = [r'\d{2,5}-\d{2,4}-\d{4}|\(\d{4}\)\d{2}-\d{4}|\d{4}-\d{6}']
# day_match_list = [r'\d{4}[/年-]\d{1,2}[/月-]\d{1,2}[日]?']
day_match_list = [r'\d{2,4}[年][^年月日]*\d{1,2}[月][^年月日]*\d{1,2}[日]|\d{2,4}/\d{2}/\d{2}']
small_price_list = [r"小.*計|お.*買.*上.*¥"]
tax_price_list = [r".*外.*税|.*内.*税|.*消.*費.*税|.*税.*金|.*税.*額|8%対象|10%対象"]
discount_price_list = [r".*値.*引|.*奉.*仕.*額"]
total_price_list = [r"(?<!.)合.*計"]

# Special
# price_list = [r"(¥\d+,\d+|¥\d+|¥-\d+|\d+円)"]
price_list = [r"[¥\\\\][0-9,.]+|\d{1,3}(?:[,.]\d{3})+|[0-9,.]+円"]


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

class ReceiptInfo:
    def __init__(self, lines) -> None:
        self.lines = lines

    def find_comapy_name(self, res, regname):
        soup = BeautifulSoup(res, 'html.parser')
        company_name = "" 
        dt_element = soup.find_all('dt')
        for element in dt_element:
            if "事業者名" in element.text:
                if element.find('a', class_='result',href=lambda href: href and regname in href):
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
        'number': phonenumber
        }
        response = requests.get(api_url, params=params, headers = {
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
    
    def get_total_idx(self):
        total_idx = -1
        for idx, line in enumerate(self.lines):
            total_price = self.find_val(line, total_price_list)
            if len(total_price) > 0:
                total_idx = idx
                break
        return total_idx
    
    def get_small_idx(self):
        small_idx = -1
        for idx, line in enumerate(self.lines):
            total_price = self.find_val(line, small_price_list)
            if len(total_price) > 0:
                small_idx = idx
                break
        return small_idx
    
    def get_small_tax_idx(self):
        tax_idx = -1
        for idx, line in enumerate(self.lines):
            total_price = self.find_val(line, tax_price_list)
            if len(total_price) > 0:
                tax_idx = idx
                break
        return tax_idx
    
    def get_date_idx(self):
        date_idx = -1
        for idx, line in enumerate(self.lines):
            total_price = self.find_val(line, day_match_list)
            if len(total_price) > 0:
                date_idx = idx
                break
        return date_idx
     
    def get_item_index_loop(self, index):
        index_loop = []
        arrTmp = []
        first_line = -1
        end_line = -1

        first_line = self.get_date_idx() + 1
        arrTmp.append(self.get_total_idx())
        arrTmp.append(self.get_small_idx())
        arrTmp.append(self.get_small_tax_idx())
        filtered_numbers = [num for num in arrTmp if num != -1]
        end_line = min(filtered_numbers)
        index_loop.append(first_line)
        index_loop.append(end_line)
        return index_loop
  
    def get_partern(self, type, title_idx):
        val = ""
        index = -1
        array_text = []
        muti_val = []
        total_check = False
        small_check = False
        first_price_check = False
        phone_number = ""
        target = ""    

        for idx, line in enumerate(self.lines):
            total_price_val = self.find_val(line, total_price_list)
            small_price_val = self.find_val(line, small_price_list)
            first_item = self.find_val(line, price_list)
            if len(total_price_val) > 0 and total_check == False:
                total_check = True

            if len(small_price_val) > 0 and total_check == False:
                small_check = True

            if len(first_item) > 0 and first_price_check == False and title_idx == 4:
                first_price_check = True
                index = idx
                break  

            if title_idx == 1 and len(target) > 0:
                phone_number = target
                break

            if title_idx == 13 and total_check == True:
                break

            # if title_idx == 14 and (small_check == False or total_check == True) :
            #     continue

            if title_idx == 15 and total_check == True:
                index = idx
                array_text.append(index)
                break

            if title_idx == 16 and total_check == False:
                continue

            target = self.find_val(line, type)       
            if len(target) > 0:
                index = idx
                array_text.append(index)
                
        if title_idx == 0:
            if len(array_text) == 0:
                val = ""
            else:    
                val = self.find_val(self.lines[array_text[0]], number_company_list)

        if title_idx == 1:
            val = self.get_company_name(phone_number)

        if title_idx == 2:
            if len(array_text) == 0:
                val = ""
            else:    
                val = self.find_val(self.lines[array_text[0]], day_match_list)

        if title_idx == 4:
            muti_val = self.get_item_index_loop(index) 
            return muti_val         

        if title_idx == 12:
            # muti_val = self.get_muti_val(array_text)
            val = self.find_val(self.lines[index], price_list)

        if title_idx == 13:
            muti_val = self.get_muti_val(array_text)

        if title_idx == 14:
            muti_val = self.get_muti_val(array_text)

        if title_idx == 15:
            val = self.find_val(self.lines[index], price_list)
            # val = self.lines[index]

        if title_idx == 16:
             muti_val = self.get_muti_val(array_text)
            # val = self.lines[index]

        if index == -1:
            val = ""
            
        result_arr = []
        if len(muti_val) > 0:
            for e in muti_val:
                data = []
                data.append(e[0])
                data.append(e[1])
                result_arr.append(data)   
        else: 
            if len(val) > 0:  
                # result_arr.append("[{}]: {}\n".format(receipt_keys[title_idx], val))
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
            data = response.text.strip().split(',')  # Chuyển đổi phản hồi thành đối tượng JSON
            company_name = data[9].replace("\"", "")
        return company_name         
    
    def getInfo(self):
        infoVal = {
        }
        # 適格請求書発行者番号
        company_number = self.get_partern(number_company_list, 0)
        infoVal[receipt_keys[0]] = company_number
        # 取引先
        company_name = self.get_partern(phone_match_list, 1)
        if len(company_name) == 0:
            company_name = self.call_houjin_number(re.sub(r'T', '', company_number[0]))
        infoVal[receipt_keys[1]] = company_name
        # 取引日付
        infoVal[receipt_keys[2]] = self.get_partern(day_match_list, 2)
        # 小計金額
        small_price = self.get_partern(small_price_list, 12)
        infoVal[receipt_keys[12]] = small_price    
        # 小計消費税金額
        tax1 = self.get_partern(tax_price_list, 13)
        infoVal[receipt_keys[13]] = tax1
        # 小計値引き額
        discount1 = self.get_partern(discount_price_list, 14)
        infoVal[receipt_keys[14]] = discount1
        #合計金額
        total_price = self.get_partern(total_price_list, 15)
        infoVal[receipt_keys[15]] = total_price    
        # 合計消費税金額
        tax2 = self.get_partern(tax_price_list, 16)
        if len(small_price) == 0 and len(tax1) > 0 and len(tax2) == 0:
            tax2 = tax1
            infoVal[receipt_keys[13]] = ""
        infoVal[receipt_keys[16]] = tax2
            
        # infoVal.append("{}{}{}{}{}{}{}{}".format(company_number, company_name, receipt_day, small_price, tax1, discount1, total_price, tax2))
        # infoVal.append("[明細情報]:\n")
        infoVal["明細情報"] = self.show_detail_item()
        json_data = json.dumps(infoVal, ensure_ascii=False, indent=4)
        file_path = "data.json"
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json_file.write(json_data)

        return json_data
    
    def conv_line_to_turtle(self, text):
        detailItem = {}
        detailItem["name"] = ""
        price = self.find_val(text, price_list)
        detailItem["price"] = price
        if len(price) > 0:
            detailItem["name"] = text.replace(price, "")
        return detailItem

    def show_detail_item(self):
        arrVal = []
        itemTmp = {}
        arr_idx_loop = self.get_partern(price_list, 4)
        for i in range(arr_idx_loop[0], arr_idx_loop[1]):
            bCheck = self.find_val(self.lines[i], price_list)
            if len(bCheck) == 0:
                continue
            itemTmp = self.conv_line_to_turtle(self.lines[i])
            arrVal.append(itemTmp)          
        return arrVal
        
def getResult(file_byte_data):
    # start_time = time.time()
    content = vision_doc_detect.detect_text(file_byte_data)
    all_text = [item[0] for item in content]
    obj = ReceiptInfo(all_text)
    return obj.getInfo()
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f"Times: {elapsed_time}s")    