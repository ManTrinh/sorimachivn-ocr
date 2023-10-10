import re
import requests
from bs4 import BeautifulSoup
import vision_doc_detect

api_url = 'http://www.jpnumber.com/searchnumber.do?'     
def get_company_name(phonenumber):
    company_name = ""
    regname = "numberinfo_{}.html".format(phonenumber).replace("-", "_")
    params = {
    'number': phonenumber
    }
    response = requests.get(api_url, params=params, headers = {
        'User-Agent': 'Chrome/94.0.4606.71',
    })

    if response.status_code == 200:
        data = response.text
        company_name = find_comapy_name(data, regname)
    return company_name    

def find_comapy_name(res, regname):
    soup = BeautifulSoup(res, 'html.parser')
    company_name = "" 
    dt_element = soup.find_all('dt')
    for element in dt_element:
        if "事業者名" in element.text:
            if element.find('a', class_='result',href=lambda href: href and regname in href):
                company_name = element.text
    return company_name.replace("事業者名：", "")        


phone_match_list = [r'\d{2,5}-\d{2,4}-\d{4}']
day_match_list = [r'\d{4}[/年-]\d{1,2}[/月-]\d{1,2}[日]?']
small_price_list = [r"小計\.*"]
tax_price_list = [r"外税|外税|消費税|税金"]
discount_price_list = [r"値引|奉仕額"]
total_price_list = [r"(?<!\S)合計"]

#Special
# -?\d+|\¥\d+
price_list = [r"(¥\d+,\d+|¥\d+|¥-\d+)"]


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

# Phương thức của lớp để in thông tin của người
def find_val(text, reg):
    for element in reg:
        matches = re.findall(element, text)
    result = "".join(matches)
    if reg == price_list:
        if len(matches) > 1:
            result = matches[len(matches) - 1]
    return result

all_text = """ヤオコー
MARKETPLACE
お取替えは1週間以内にお願いします
一部商品は除きます
八潮店TEL048-994-4811
< 領収証 >
ご利用ありがとうございます。
営業時間は、朝9時半より
夜10時までとさせて頂きます。
2018年12月02日(日) レジNo:0005
貴:おく
11プレミアムソフト ¥288
19タンレイG500*6 ¥1,038
11キュキュジヨキンカエJ ¥298
09ハコダテカレーチュウ ¥350
09ビーフスパイシー ¥298
14コロッケ ¥99
14ローストンカツ ¥368
03PBパリットイタリアン ¥138
02カマアゲシラス ¥171
04ユニュウタネナシクロブ ¥337
13アキタアカタマゴ10コ ¥198
09エヒメポンカンサイダ ¥84
19タカラセトウチL350 ¥128
19ヒヨウケツGF500 ¥148
03タマネギバラ ¥69
13ヤオコーサキュウラツキヨ ¥248
外税(対象 ¥4,260) ¥340
合計 ¥4,600
現金 ¥10,000
お預り合計 ¥10,000
お釣り ¥
5,400
*********ポイント情報*********
通常P ¥
4,26021P
今回ポイント
21P
累計ポイント
490P
当月お買上累計額
¥4,260
※ポイント除外商品は含み
ません
カードNo. 2000024649542
上記正に領収いたしました
レシートNo:7891 16点買
16:43TM"""

# lines = all_text.replace(" ","").strip().split('\n')
lines = all_text.strip().split('\n')
gokei_index = 0

def get_partern(type, title_idx):
    val = ""
    index = -1
    array_text = []
    muti_val = []
    total_check = False
    small_check = False
    phone_number = ""
    target = ""

    for idx, line in enumerate(lines):
        total_price_val = find_val(line, total_price_list)
        small_price_val = find_val(line, small_price_list)
        if len(total_price_val) > 0 and total_check == False:
            total_check = True

        if len(small_price_val) > 0 and total_check == False:
            small_check = True    

        if title_idx == 1 and len(target) > 0:
            phone_number = target
            break

        if title_idx == 13 and total_check == True:
            break

        if title_idx == 14 and (small_check == False or total_check == True) :
            continue

        if title_idx == 16 and total_check == False:
            continue

        target = find_val(line, type)       
        if len(target) > 0:
            index = idx
            array_text.append(index)

    if title_idx == 1:
        val = get_company_name(phone_number)
    if title_idx == 2:
        val = find_val(lines[array_text[0]], day_match_list)      
    if title_idx == 12:
        muti_val = get_muti_val(array_text)
    if title_idx == 13:
        muti_val = get_muti_val(array_text)
    if title_idx == 14:
        muti_val = get_muti_val(array_text)
    if title_idx == 15:
        val = find_val(lines[index], price_list)
    if title_idx == 16:
        val = find_val(lines[index], price_list)
    
    if index == -1:
        val = ""
    if len(muti_val) > 0:
        for e in muti_val:
            print("{}:{} {}".format(receipt_keys[title_idx],e[0], e[1]))
    else:    
        print("{}:{}".format(receipt_keys[title_idx], val))

def get_muti_val(arrVal):
    muti_val = []
    for pos in arrVal:
        val_tmp = []
        price_tmp = find_val(lines[pos], price_list)
        name_tmp = lines[pos].replace(price_tmp, "")
        val_tmp.append(name_tmp)
        val_tmp.append(price_tmp)
        muti_val.append(val_tmp)
    return muti_val         

# 0	    適格請求書発行者番号
# 1	    取引先
# 2	    取引日付               day_match_list
# 3	    件名（決済理由）
# 4	    番号
# 5	    商品名
# 6	    単価
# 7	    単位
# 8	    数量
# 9	    金額
# 10	割引⾦額
# 11	消費税情報
# 12	小計金額               small_price_list
# 13	小計消費税金額
# 14	小計値引き額
# 15	合計金額
# 16	合計消費税金額

# 取引先
get_partern(phone_match_list, 1)
# 取引日付
get_partern(day_match_list, 2)
# 小計金額
get_partern(small_price_list, 12)    
# 小計消費税金額
get_partern(tax_price_list, 13)
# 小計値引き額
get_partern(discount_price_list, 14)
#合計金額
get_partern(total_price_list, 15)    
# 合計消費税金額
get_partern(tax_price_list, 16) 

