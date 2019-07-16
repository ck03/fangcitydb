import json
import requests
from lxml import etree
from pymongo import MongoClient
import time
from copy import deepcopy


class GetCityName():
    def __init__(self):
        self.url = "https://www.fang.com/SoufunFamily.htm"
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"}
        self.client = MongoClient(host="127.0.0.1", port=27017)
        self.collection = self.client["fang"]["city"]

    def parse_url(self, url):
        response = requests.get(url, headers=self.headers)
        return response.content.decode(encoding="gbk", errors="ignore")

    def dbexit(self):
        collection = self.client["fang"]["city"]
        if collection.count() > 0:
            collection.drop()
            print("已刪除Mogodb_fang_city")
        else:
            print("Mogodb_fang_city不存")

    def save_dict(self, dict_json):
        with open("fang房天下city.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(dict_json, ensure_ascii=False, indent=2))

    def findnewesf(self, url):
        s = url.find(".")
        if url[-1] == "/":
            new_s = url[:s+1] + "newhouse." + url[s+1:] + "house/s/"
        else:
            new_s = url[:s + 1] + "newhouse." + url[s + 1:] + "/house/s/"
        esf_s = url[:s+1]+"esf."+url[s+1:]
        if new_s == "http://bj.newhouse.fang.com/house/s/":
            new_s = "http://newhouse.fang.com/house/s/"
        if esf_s == "http://bj.esf.fang.com/":
            esf_s = "http://esf.fang.com/"
        return new_s, esf_s

    def run(self):  # 主要實現邏輯
        # 判斷是否有該db
        self.dbexit()
        # 1.建構url
        # 2.歷遍,發送請求,獲取響應
        ret = self.parse_url(self.url)
        # print(ret)
        html_str = etree.HTML(ret)
        tr_list = html_str.xpath("//div[@class='outCont']/table//tr")
        print(len(tr_list))
        tr_id = ""
        tr_id_temp = ""
        td_dict = {}
        td_dict_json = {}
        city_list = []
        result_list = []
        result_list_json = []
        result_dict = {}
        for tr in tr_list:
            tr_id = tr.xpath("./@id")[0]
            # 第二列也是同一省份
            if tr_id_temp == tr_id or tr_id_temp == "":
                if tr_id_temp == "":
                    td_dict["province_e"] = tr.xpath("./td[1]/text()")[0].strip()
                    td_dict["province_c"] = tr.xpath("./td[2]//text()")[0]

                tr_id_temp = tr_id
                a_list = tr.xpath("./td[3]/a")
                for a in a_list:
                    a_dict = {}
                    a_dict["name"] = a.xpath("./text()")[0]
                    a_dict["url"] = a.xpath("./@href")[0]
                    a_dict["url"] = a_dict["url"].strip()
                    if a_dict["name"] != "昌吉" and a_dict["name"] != "吴江":
                        a_dict["new_url"], a_dict["esf_url"] = self.findnewesf(a_dict["url"])
                    elif a_dict["name"] == "昌吉":
                        a_dict["new_url"] = "https://changji.newhouse.fang.com/house/s/"
                        a_dict["esf_url"] = "https://changji.esf.fang.com/"
                    elif a_dict["name"] == "吴江":
                        a_dict["new_url"] = "https://suzhou.newhouse.fang.com/house/s/"
                        a_dict["esf_url"] = "https://suzhou.esf.fang.com/house-a0584/?_rfss=1&amp;_rfss=1&amp;_rfss=1"

                    city_list.append(a_dict)
            else:
                # 寫進檔案或Insert to Db的時候
                str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
                int_t = int(str_time)
                td_dict["time"] = int_t
                td_dict["city"] = city_list
                # 要用deepcopy,複製另一份,否則仍會被修改
                td_dict_json = deepcopy(td_dict)
                result_list_json.append(td_dict_json)
                result_list.append(td_dict)

                # insert 到mongodb時會增加 "_id": ObjectId(....)
                # 導致若是要存成json檔時,會失敗,滿困擾的
                self.collection.insert(td_dict)

                td_dict = {}
                td_dict_json = {}
                city_list = []
                try:
                    if len(tr.xpath("./td[1]/text()")) != 0:
                        td_dict["province_e"] = tr.xpath("./td[1]/text()")[0].strip()
                    else:
                        td_dict["province_e"] = ""
                    td_dict["province_c"] = tr.xpath("./td[2]//text()")[0]
                except:
                    print(tr.xpath("./td[1]/text()"))
                    print(len(result_list))
                    result_dict["Result"] = result_list
                    print(result_dict)
                tr_id_temp = tr_id
                a_list = tr.xpath("./td[3]/a")
                for a in a_list:
                    a_dict = {}
                    a_dict["name"] = a.xpath("./text()")[0]
                    a_dict["url"] = a.xpath("./@href")[0]
                    a_dict["url"] = a_dict["url"].strip()
                    if a_dict["name"] != "昌吉" and a_dict["name"] != "吴江":
                        a_dict["new_url"], a_dict["esf_url"] = self.findnewesf(a_dict["url"])
                    elif a_dict["name"] == "昌吉":
                        a_dict["new_url"] = "https://changji.newhouse.fang.com/house/s/"
                        a_dict["esf_url"] = "https://changji.esf.fang.com/"
                    elif a_dict["name"] == "吴江":
                        a_dict["new_url"] = "https://suzhou.newhouse.fang.com/house/s/"
                        a_dict["esf_url"] = "https://suzhou.esf.fang.com/house-a0584/?_rfss=1&amp;_rfss=1&amp;_rfss=1"

                    city_list.append(a_dict)
        # 最後一欄不要忘了寫入
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        int_t = int(str_time)
        td_dict["time"] = int_t
        td_dict["city"] = city_list
        td_dict_json = deepcopy(td_dict)
        result_list_json.append(td_dict_json)
        result_list.append(td_dict)
        self.collection.insert(td_dict)
        result_dict["Result"] = result_list_json
        print(result_list_json)
        # 3.取得數據
        # 4.保存(json檔,mongodb)
        self.save_dict(result_dict)


if __name__ == "__main__":
    getcityname = GetCityName()
    getcityname.run()



# json_str = {
#     "Result":
#     [
#         {
#             "province_e": "A",
#             "province_c": "安徽",
#             "city": [
#                      {"name": "合肥", "url": "http://hf.fang.com/"},
#                      {"name": "芜湖", "url": "http://wuhu.fang.com/"}
#               ]
#
#         },
#         {
#             "top1": "福建",
#             "top2": ["福州", "厦门", "泉州"]
#         }
#     ]
# }
#
# json_dict = json.dumps(json_str, ensure_ascii=False)
# print(json_dict)