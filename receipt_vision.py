import re
import requests
from bs4 import BeautifulSoup
import vision_doc_detect
api_url = 'http://www.jpnumber.com/searchnumber.do?'

# Reg
number_company_list = [r"T\d{13}"]
phone_match_list = [r'\d{2,5}-\d{2,4}-\d{4}|\(\d{4}\)\d{2}-\d{4}']
# day_match_list = [r'\d{4}[/年-]\d{1,2}[/月-]\d{1,2}[日]?']
day_match_list = [r'\d{2,4}[年][^年月日]*\d{1,2}[月][^年月日]*\d{1,2}[日]']
small_price_list = [r"小.*計"]
tax_price_list = [r".*外.*税|.*内.*税|.*消.*費.*税|.*税.*金"]
discount_price_list = [r".*値.*引|.*奉.*仕.*額"]
total_price_list = [r".*合.*計"]

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
            val_tmp.append(name_tmp)
            val_tmp.append(price_tmp)
            muti_val.append(val_tmp)
        return muti_val
    
    def get_item_index_loop(self, index):
        index_loop = []
        next_price_item = ""
        next_price_idx = -1
        first_line_item_idx = -1
        item_loop = -1
        itemCheck = False
        totalCheck = False
        smallCheck = False
        taxCheck = False
        total_price_idx = -1
        small_price_idx = -1
        tax_price_idx = -1
        end_line_item_idx = -1
        for idx, line in enumerate(self.lines):
            next_price_item = self.find_val(line, price_list)
            total_price = self.find_val(line, total_price_list)
            small_price = self.find_val(line, small_price_list)
            tax_price = self.find_val(line, tax_price_list)
            if len(next_price_item) > 0 and itemCheck == False and idx > index:
                itemCheck = True
                next_price_idx = idx
                item_loop = next_price_idx - index

            if len(tax_price) > 0 and taxCheck == False:
                tax_price_idx = idx
                taxCheck = True

            if len(small_price) > 0 and smallCheck == False:
                small_price_idx = idx
                smallCheck = True    

            if len(total_price) > 0 and totalCheck == False:
                total_price_idx = idx
                totalCheck = True


        if small_price_idx > 0:
            end_line_item_idx = small_price_idx
        if small_price_idx < 0 and tax_price_idx > 0 and tax_price_idx < total_price_idx:
            end_line_item_idx = tax_price_idx
        if small_price_idx < 0 and tax_price_idx > 0 and total_price_idx < tax_price_idx:
            end_line_item_idx = total_price_idx
        if tax_price_idx < 0 and small_price_idx < 0 and total_price_idx > 0:
            end_line_item_idx = total_price_idx    

        distance = end_line_item_idx % item_loop      
        end_line_item_idx = end_line_item_idx - distance

        if item_loop > 1:
            first_line_item_idx = index - item_loop + 1
        else:        
            first_line_item_idx = index
        index_loop.append(item_loop)
        index_loop.append(first_line_item_idx)        
        index_loop.append(end_line_item_idx)        
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

            if title_idx == 14 and (small_check == False or total_check == True) :
                continue

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
            # val = self.find_val(self.lines[index], price_list)
            val = self.lines[index]

        if index == -1:
            val = ""
        result_arr = []
        if len(muti_val) > 0:
            result_arr.append("[{}]\n".format(receipt_keys[title_idx]))
            for e in muti_val:
                # result_arr.append("{}:{} {}\n".format(receipt_keys[title_idx],e[0], e[1]))
                result_arr.append("{}: {}\n".format(e[0], e[1]))   
        else: 
            if len(val) > 0:  
                result_arr.append("[{}]: {}\n".format(receipt_keys[title_idx], val))
        return result_arr          
    
    def getInfo(self):
        infoVal = []
        # 取引先
        company_number = "".join(self.get_partern(number_company_list, 0))
        # 取引先
        company_name = "".join(self.get_partern(phone_match_list, 1))
        # 取引日付
        receipt_day = "".join(self.get_partern(day_match_list, 2))
        # 小計金額
        small_price = "".join(self.get_partern(small_price_list, 12))    
        # 小計消費税金額
        tax1 = "".join(self.get_partern(tax_price_list, 13))
        # 小計値引き額
        discount1 = "".join(self.get_partern(discount_price_list, 14))
        #合計金額
        total_price = "".join(self.get_partern(total_price_list, 15))    
        # 合計消費税金額
        tax2 = "".join(self.get_partern(tax_price_list, 16))
        if len(small_price) == 0 and len(tax1) > 0 and len(tax2) == 0:
            tax2 = tax1.replace(receipt_keys[13], receipt_keys[16])
            tax1 = ""
        infoVal.append("{}{}{}{}{}{}{}{}".format(company_number, company_name, receipt_day, small_price, tax1, discount1, total_price, tax2))
        infoVal.append("[明細情報]:\n")
        infoVal.append(self.show_detail_item())
        return "".join(infoVal)

    def show_detail_item(self):
        detailVal = []
        test = self.get_partern(price_list, 4)
        for i in range(test[1], test[2], test[0]):
            for j in range(i, i + test[0]):
                detailVal.append(self.lines[j])
                detailVal.append("\n")      
        return "".join(detailVal)
        
def getResult(file_byte_data):
    # start_time = time.time()
    content = vision_doc_detect.detect_text(file_byte_data).strip().split('\n')
    obj = ReceiptInfo(content)
    return obj.getInfo()
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f"Times: {elapsed_time}s")    