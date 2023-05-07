import json
import requests
import re
import uuid
import hashlib
import time
from knowledge2db.config import YOUDAO_URL, APP_KEY, APP_SECRET, CAIYUN_KEY, debug

# split the source into chunks of 5000 characters
def __list_splitter(l):
    if len("".join(l)) < 5000:
        return [l]
    else:
        return __list_splitter(l[:len(l)//2]) + __list_splitter(l[len(l)//2:])

def __remove_special(one_string):
    other_strings = ["..", "……", ".."]
    for other_string in other_strings:
        if other_string in one_string:
            return "other"
    # remove all special characters (not chinese) with space
    one_string = re.sub("[（|）|(|)|、|，|?|']", " ", one_string)
    one_string = re.sub("&", " and ", one_string)
    one_string = re.sub("-", "_", one_string)
    one_string = re.sub("/", "or", one_string)
    return one_string

def __convert_naming(one_string, naming="camel"):
    # naming: camel, lower_case_with_underscores
    one_string = __remove_special(one_string)

    string_list = re.split(" |/|,|\n", str(one_string))
    if naming == "camel":
        first = string_list[0].lower()
        others = string_list[1:] 
    
        others_capital = [word.capitalize() for word in others]
        others_capital[0:0] = [first]
    
        return ''.join(others_capital)
    
    elif naming == "lower_case_with_underscores":
        result =  '_'.join(string_list).lower()
        result = re.sub("\_+", "_", result)
        return result
    else:
        raise ValueError("naming must be camel or lower_case_with_underscores")
       
def __encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()
 
def __truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]
 
def __do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_URL, data = data, headers = headers)

def caiyun_translate(source, naming="camel"):
    # source: list of strings
    # return: list of strings in English and CamelCase
    url = "http://api.interpreter.caiyunai.com/v1/translator"

    payload = {
        "source": source,
        "trans_type": "auto2en",
        "request_id": "demo",
        "detect": True,
    }

    headers = {
        "content-type": "application/json",
        "x-authorization": "token " + CAIYUN_KEY,
    }

    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)

    if naming == "camel":
        return [__convert_naming(phrase, naming) for phrase in json.loads(response.text)["target"]] 
    else:
        return json.loads(response.text)["target"]
 
def youdao_translate(source, naming="camel"):
    if not APP_KEY or not APP_SECRET:
        raise ValueError("APP_KEY and APP_SECRET must be set in config file")
    def translate(qArray):
        data = {}
        data['from'] = 'zh-CHS'
        data['to'] = 'en'
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = APP_KEY + __truncate(''.join(qArray)) + salt + curtime + APP_SECRET
        sign = __encrypt(signStr)
        data['appKey'] = APP_KEY
        data['q'] = qArray
        data['salt'] = salt
        data['sign'] = sign
        data['vocabId'] = "B7BFB26EDABC49C68A5A6557682CD88D"
        r = json.loads(__do_request(data).content.decode('utf-8'))
        if naming:
            return [__convert_naming(i["translation"], naming) for i in r["translateResults"]] 
        else:
            return [__remove_special(i["translation"]) for i in r["translateResults"]] 

    # add a loop to retry translation if the result is not correct (i.e, the vocab is not loaded)
    # retry_needed = True
    # while retry_needed:
    source_lists = __list_splitter(source)
    target_lang_terms = []
    for source_list in source_lists:
        target_lang_terms += translate(source_list)
        # if not naming and 'base attributes' not in target_lang_terms:
        #     retry_needed = True
        # elif naming == "camel" and 'baseAttributes' not in target_lang_terms:
        #     retry_needed = True
        # elif naming == "lower_case_with_underscores" and 'base_attributes' not in target_lang_terms:
        #     retry_needed = True
        # else:
        #     retry_needed = False

    return target_lang_terms


if __name__ == "__main__":
    source = ["智慧城市", "基础属性", "智慧城市知识体系", '人-地']
    target = caiyun_translate(source)

    print("彩云", target)
    print("有道", youdao_translate(source))
