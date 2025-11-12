# -*- coding: utf-8 -*-
##### Application Insights (Azure Monitor) #####
from azure.identity import DefaultAzureCredential
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
# os.chdir("c:/Users/gina3_wang/OneDrive - ASUS/Folder/任務/20240103_email copilot/email_copilot")
# import config # 跑單一檔案測試時候要導入環境變數

import os

sub_id:str = os.getenv("MYAPP_AZURE_SUBSCRIPTION_ID") # type: ignore[assignment]
client = ApplicationInsightsManagementClient(credential=DefaultAzureCredential(), subscription_id=sub_id)
################################################

import json
import re
import time
import asyncio
import traceback # for error handling
from contextvars import ContextVar
import openai

from api1_v3.get_summary import gpt_summary
from api1_v3.get_translate import gpt_translate
from api1_v3.get_split import gpt_split
from api1_v3.check_vector import call_redis_api, initialize_client_http, close_client_http
from api1_v3.product_line_mapping import find_productline
from api1_v3.write_cosmos import write_cosmosDB
from api1_v3.call_gpt import initialize_client_gpt4o

class Api1_process():
    def __init__(self):
        self.txt_ = []
        self.request_logs: ContextVar[list] = ContextVar("request_logs", default=[]) # 不同asyncio的request_logs
        self.generated_check_info_error_log = []
        self.summary = None   # 遇到gpt_policy的問題時候 至少有summary可以使用
        self.start_t = 0
        self.lang = 'error'
        self.product_line = 'error'

    def time_test(self, x = time.time(), str_="", y=0):
        a = time.time()
        if str_:
            print('>'*y, round(a-x, 4), str_)
            str_ = '>'*y + str_
            write_data = {'py':str_, 'time':a, 'diff_':round(a-x, 4)}
            self.txt_.append(write_data)
        return a

    def get_summary(self):
        return self.summary
    
    def get_start_t(self):
        return self.start_t
    
    def get_lang(self):
        return self.lang
    
    def get_product_line(self):
        return self.product_line

    async def call_api_process(self, sentence_org, product_line, website):
        translate_result = await gpt_translate(sentence_org)
        api_return, api_intent_result, api_kb_result= await call_redis_api(quest = translate_result, product_line = product_line, website = website)
        return translate_result, api_return, api_intent_result, api_kb_result

    async def generated_check_info(self, input_product_content, product_line, site):
        time_ = self.time_test()
        summary, lang, saummary_json = await gpt_summary(input_product_content)
        self.summary = summary
        self.lang = lang
        time_ = self.time_test(x = time_, str_="gpt_summary", y=4)
        extra_summary = {
            "summary": asyncio.create_task(
                self.call_api_process(
                    sentence_org = summary, 
                    product_line = product_line, 
                    website = site))
                    }
        split_json = await gpt_split(email_content_input = input_product_content, lang = lang)
        time_ = self.time_test(x = time_, str_="gpt_split", y=4)
        split_json = json.loads(split_json)
        split_task = {
                key: asyncio.create_task(
                    self.call_api_process(
                        sentence_org = value, 
                        product_line = product_line, 
                        website = site))
                for key, value in split_json.items()
                if re.match(r'extracted_sentence(\d+)', key)
            }
        split_task.update(extra_summary)
        split_task_result = await asyncio.gather(*split_task.values())
        time_ = self.time_test(x = time_, str_="split & summary gpt_translate, api_intent, api_kb", y=4)

        # 先把api結果存起來
        api_log_list = [value[1] for value in split_task_result]
        logs = self.request_logs.get()
        logs.append(api_log_list)

        # 確認api是否有順利執行
        api_kb_log_check = [0 if value[1]['success'] ==True else 1 for value in split_task_result]
        # print(split_task_result)
        if sum(api_kb_log_check) > 0:
            raise RuntimeError('API call error')
        time_ = self.time_test(x = time_, str_="check api result", y=4)

        translate_list = [value[0] for value in split_task_result]
        api_intent_list = [value[2] for value in split_task_result]
        api_kb_list = [value[3] for value in split_task_result]
        extract_type = ['split' if 'extracted_sentence' in key else 'summary' for key in split_task.keys()]
        extract_type_num = [int(key[-1]) if 'extracted_sentence' in key else None for key in split_task.keys()]
        split_json_keys = [key for key in split_task.keys()]

        email_split_info = []
        for split_json_keys, translate, api_log, api_intent, api_kb, extract_type, extract_type_num in zip(split_json_keys, 
                                                                                                            translate_list,
                                                                                                            api_log_list,
                                                                                                            api_intent_list,
                                                                                                            api_kb_list,
                                                                                                            extract_type,
                                                                                                            extract_type_num):
            try:
                gpt_org = split_json.get(split_json_keys, summary)
                api_intent['intent_1']
                api_intent['cosineSimilarity_1']
                api_intent['key_1']
            except:
                self.generated_check_info_error_log.append({
                    "split_json_keys": split_json_keys,
                    "translate": translate,
                    "api_log": api_log,
                    "api_intent": api_intent,
                    "api_kb": api_kb,
                    "extract_type": extract_type,
                    "extract_type_num": extract_type_num
                })
                raise Exception('generated check info ERROR')
            email_split_info_ = {
                "extract_type": extract_type,
                "extract_type_num": extract_type_num,
                "gpt_output_org":gpt_org, 
                "gpt_output": translate, 
                "intent":api_intent['intent_1'],
                "intent_similarity":api_intent['cosineSimilarity_1'],
                "intent_key":api_intent['key_1'],
                "top1_kb":api_kb['kb_no_1'],
                "top1_kb_similarity":api_kb['cosineSimilarity_1'],
                "key_1":api_kb['key_1'],
                "top2_kb":api_kb['kb_no_2'],
                "top2_kb_similarity":api_kb['cosineSimilarity_2'],
                "key_2":api_kb['key_2'],
                "top3_kb":api_kb['kb_no_3'],
                "top3_kb_similarity":api_kb['cosineSimilarity_3'],
                "key_3":api_kb['key_3'],
                "top4_kb":api_kb['kb_no_4'],
                "top4_kb_similarity":api_kb['cosineSimilarity_4'],
                "key_4":api_kb['key_4'],
                "api_log": api_log,
                
            }
            email_split_info.append(email_split_info_)
        return email_split_info, lang, summary

    def generated_gpt_extract(self, email_split_info):
        # case1 留下split 技術支援 >= 0.71(0.9) or 分技術支援(不是only chat greeting) >= 0.6(0.87)
        output_list_case1 = []
        for lst in email_split_info:
            if lst['extract_type']=='summary':
                continue
            if lst['intent'] == 'Only Chat':
                continue
            if lst['intent'] == 'Greeting':
                continue
            if lst['intent'] != 'Technical Support':
                if lst['intent_similarity'] >= 0.6:
                    tmp_dict = {
                        "extract_type": lst['extract_type'],
                        "extract_type_num": lst['extract_type_num'],
                        "gpt_output" : lst['gpt_output_org'],
                        "intent": lst['intent'],
                        "top1_simi": lst['top1_kb_similarity'],
                        "top1_kb": lst['top1_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top2_kb": lst['top2_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top3_kb": lst['top3_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top4_kb": lst['top4_kb'] if lst['intent'] == 'Technical Support' else None
                    }
                    output_list_case1.append(tmp_dict)
                else:
                    pass
            else:
                if lst['top1_kb_similarity'] >= 0.71:
                    tmp_dict = {
                        "extract_type": lst['extract_type'],
                        "extract_type_num": lst['extract_type_num'],
                        "gpt_output" : lst['gpt_output_org'],
                        "intent": lst['intent'],
                        "top1_simi": lst['top1_kb_similarity'],
                        "top1_kb": lst['top1_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top2_kb": lst['top2_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top3_kb": lst['top3_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top4_kb": lst['top4_kb'] if lst['intent'] == 'Technical Support' else None
                    }
                    output_list_case1.append(tmp_dict)
                else:
                    pass
        # case2 split ts >= 0.695 (0.89)
        note_case2_max_similarity = 0
        for lst in email_split_info:
            if lst['extract_type']=='summary':
                continue
            if (lst['intent'] == 'Technical Support') & (lst['top1_kb_similarity'] >= 0.695):
                if lst['top1_kb_similarity'] > note_case2_max_similarity:
                    note_case2_max_similarity = lst['top1_kb_similarity']
                    tmp_dict = {
                        "extract_type": lst['extract_type'],
                        "extract_type_num": lst['extract_type_num'],
                        "gpt_output" : lst['gpt_output_org'],
                        "intent": lst['intent'],
                        "top1_simi": lst['top1_kb_similarity'],
                        "top1_kb": lst['top1_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top2_kb": lst['top2_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top3_kb": lst['top3_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top4_kb": lst['top4_kb'] if lst['intent'] == 'Technical Support' else None
                    }
        output_list_case2 = [tmp_dict] if note_case2_max_similarity > 0 else []
        # case3 summary 判斷
        note_case3_target = [lst for lst in email_split_info if lst['extract_type']=='summary'][0]
        note_case3_target_intent = note_case3_target['intent']
        ## summary tech >= 0.695 (0.89)
        if (note_case3_target_intent == 'Technical Support') & (note_case3_target['top1_kb_similarity'] >= 0.695):
            note_case3_target_top1_kb = note_case3_target['top1_kb']

            note_case3_max_similarity = 0
            tmp_dict = {}
            for lst in email_split_info:
                if lst['extract_type']=='summary':
                    continue
                if (note_case3_target_intent == lst['intent']) & (note_case3_target_top1_kb == lst['top1_kb']) & (note_case3_max_similarity < lst['top1_kb_similarity']):
                    note_case3_max_similarity = lst['top1_kb_similarity']
                    tmp_dict = {
                        "extract_type": lst['extract_type'],
                        "extract_type_num": lst['extract_type_num'],
                        "gpt_output" : lst['gpt_output_org'],
                        "intent": lst['intent'],
                        "top1_simi": lst['top1_kb_similarity'],
                        "top1_kb": lst['top1_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top2_kb": lst['top2_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top3_kb": lst['top3_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top4_kb": lst['top4_kb'] if lst['intent'] == 'Technical Support' else None
                    }
            if len(tmp_dict) == 0:
                tmp_dict = {
                    "extract_type": note_case3_target['extract_type'],
                    "extract_type_num": note_case3_target['extract_type_num'],
                    "gpt_output" : note_case3_target['gpt_output_org'],
                    "intent": note_case3_target['intent'],
                    "top1_simi": lst['top1_kb_similarity'],
                    "top1_kb": note_case3_target['top1_kb'],
                    "top2_kb": note_case3_target['top2_kb'],
                    "top3_kb": note_case3_target['top3_kb'],
                    "top4_kb": note_case3_target['top4_kb']
                }
        ## summary 非tech >= 0.6 (0.87)
        elif (note_case3_target_intent != 'Technical Support') & (note_case3_target_intent != 'Only Chat')& (note_case3_target_intent != 'Greeting') & (note_case3_target['intent_similarity'] >= 0.6):
            note_case3_max_similarity = 0
            tmp_dict = {}
            for lst in email_split_info:
                if lst['extract_type']=='summary':
                    continue
                if (note_case3_target_intent == lst['intent']) & (note_case3_max_similarity < lst['intent_similarity']):
                    note_case3_max_similarity = lst['intent_similarity']
                    tmp_dict = {
                        "extract_type": lst['extract_type'],
                        "extract_type_num": lst['extract_type_num'],
                        "gpt_output" : lst['gpt_output_org'],
                        "intent": lst['intent'],
                        "top1_simi": lst['top1_kb_similarity'],
                        "top1_kb": lst['top1_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top2_kb": lst['top2_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top3_kb": lst['top3_kb'] if lst['intent'] == 'Technical Support' else None,
                        "top4_kb": lst['top4_kb'] if lst['intent'] == 'Technical Support' else None
                    }
            if len(tmp_dict) == 0:
                tmp_dict = {
                    "extract_type": note_case3_target['extract_type'],
                    "extract_type_num": note_case3_target['extract_type_num'],
                    "gpt_output" : note_case3_target['gpt_output_org'],
                    "intent": note_case3_target['intent'],
                    "top1_simi": lst['top1_kb_similarity'],
                    "top1_kb": note_case3_target['top1_kb'],
                    "top2_kb": note_case3_target['top2_kb'],
                    "top3_kb": note_case3_target['top3_kb'],
                    "top4_kb": note_case3_target['top4_kb']
                }
        ## summary 判斷是 only chat or greeting
        else:
            tmp_dict = {}
        
        if len(tmp_dict) > 0:
            output_list_case3 = [tmp_dict]    
        else:
            output_list_case3 = []
            
        if len(output_list_case1)>0:
            output_gpt_extract = output_list_case1
        elif len(output_list_case2)>0:
            output_gpt_extract = output_list_case2
        elif len(output_list_case3)>0:
            output_gpt_extract = output_list_case3
        else:
            output_gpt_extract = []
        return output_gpt_extract

    def num_recode(self, 
                   email_split_sentence: list,  # 要給客服產出的句子 output_gpt_extract
                   email_split_info: list # gpt產出的原本句子 email_split_info
                   ):
        output_email_split_sentence = {}
        index_tranfrom_dict = {}
        i_ = 1
        for item in email_split_sentence:
            raw_index = item["extract_type_num"]
            if item["intent"] == "Technical Support":
                key = item["top1_kb"]
            else:
                key = item["gpt_output"]

            if key not in output_email_split_sentence:
                output_email_split_sentence[key] = item.copy()
                output_email_split_sentence[key]["extract_type_num"] = i_
                index_tranfrom_dict[raw_index] = i_
                i_ += 1
            else:
                index_tranfrom_dict[raw_index] = output_email_split_sentence[key]["extract_type_num"]

                output_email_split_sentence[key]["gpt_output"] += " " + item["gpt_output"]

                if item["top1_simi"] > output_email_split_sentence[key]["top1_simi"]:
                    output_email_split_sentence[key]["top2_kb"] = item["top2_kb"]
                    output_email_split_sentence[key]["top3_kb"] = item["top3_kb"]
                    output_email_split_sentence[key]["top4_kb"] = item["top4_kb"]
            output_email_split_sentence[key]["extract_type"] = 'split'
        output_email_split_sentence = list(output_email_split_sentence.values())
        output_email_split_sentence = [{k: v for k, v in item.items() if k != 'top1_simi'} for item in output_email_split_sentence]

        for data in email_split_info:
            num_org = data['extract_type_num']
            if num_org in index_tranfrom_dict:
                data["extract_type_num"] = index_tranfrom_dict[num_org]
            else:
                data["extract_type_num"] = None
            data["extract_type_num_org"] = num_org
        return output_email_split_sentence, email_split_info

    def check_info_rewrite(self, email_split_info):
        split_info = []
        api_log = []
        for lst in email_split_info:
            split_info.append({
                "extract_type": lst['extract_type'],
                "extract_type_num": lst['extract_type_num'],
                "extract_type_num_org": lst['extract_type_num_org'],
                "gpt_output_org": lst['gpt_output_org'],
                "gpt_output": lst['gpt_output'],
                "intent": lst['intent'],
                'intent_similarity': lst['intent_similarity'],
                'intent_key': lst['intent_key'],
                'top1_kb': lst['top1_kb'],
                'top1_kb_similarity': lst['top1_kb_similarity'],
                'top1_kb_key': lst['key_1'],
                'top2_kb': lst['top2_kb'],
                'top2_kb_similarity': lst['top2_kb_similarity'],
                'top2_kb_key': lst['key_2'],
                'top3_kb': lst['top3_kb'],
                'top3_kb_similarity': lst['top3_kb_similarity'],
                'top3_kb_key': lst['key_3'],
                'top4_kb': lst['top4_kb'],
                'top4_kb_similarity': lst['top4_kb_similarity'],
                'top4_kb_key': lst['key_4']})
            api_log.append({
                "extract_type": lst['extract_type'],
                "extract_type_num": lst['extract_type_num_org'],
                "api_log":lst.get('api_log', {})
            })
        return split_info, api_log
    
    async def email_detect_pre(self, 
            product_type, 
            product_model, 
            problem_description_content, 
            site, case_id, 
            email_content):
        start_time_ts = int(time.time())
        self.start_t = start_time_ts

        time_ = self.time_test()
        if ((problem_description_content == None) | (problem_description_content == "")):
            problem_description_content_new = email_content
            problem_description_content_new  = re.sub(product_model, '', problem_description_content_new)
        else:
            problem_description_content_new = '[Product Information]\nProduct Type: '+product_type+'\n\n[Problem Description]\n'+problem_description_content
        time_ = self.time_test(x = time_, str_="if problem_description_content_new")

        product_line = find_productline(site, product_type)
        self.product_line = product_line
        time_ = self.time_test(x=time_, str_="product_line")

        email_split_info, lang, summary = await self.generated_check_info(
            input_product_content = problem_description_content_new,
            product_line = product_line, 
            site = site)
        time_ = self.time_test(x=time_, str_="generated_check_info")
        gpt_extract = self.generated_gpt_extract(email_split_info = email_split_info)
        time_ = self.time_test(x=time_, str_= "generated_gpt_extract")

        gpt_extract, email_split_info = self.num_recode(gpt_extract, email_split_info)
        time_ = self.time_test(x=time_, str_= "num_recode")

        split_info, api_log = self.check_info_rewrite(email_split_info)
        time_ = self.time_test(x=time_, str_= "check_info_rewrite")

        end_time_ts = int(time.time())

        if len(gpt_extract) == 0:
            gpt_extract_type = 'unclear_description'
        else:
            gpt_extract_type = 'available'

        output = {
            "case_id": case_id,
            "gpt_extract":{
                "user_summary": summary,
                "type": gpt_extract_type,
                "email_split_sentence": gpt_extract
            }, 
            "check_info":{
                "start_time_ts": start_time_ts,
                "end_time_ts": end_time_ts,
                "lang": lang,
                "product_line": product_line,
                "email_split_info":split_info
            }
        }

        return output, api_log



async def email_detect(
        _id,
        case_id, email,
        phone, case_date,site,
        product_type, email_content,
        product_model, product_sn,
        problem_description_content):
    global txt_
    input_data = {
        "case_id": case_id,
        "email": email,
        "phone": phone,
        "case_date": case_date,
        "site": site,
        "product_type": product_type,
        "email_content": email_content,
        "product_model": product_model,
        "product_sn": product_sn,
        "problem_description_content": problem_description_content
    }
    Api1 = Api1_process()

    time_ = Api1.time_test()
    initialize_client_http()
    initialize_client_gpt4o()
    time_ = Api1.time_test(x = time_, str_="initialize")

    try:
        output, api_log= await Api1.email_detect_pre(
            product_type = product_type,
            product_model = product_model,
            problem_description_content = problem_description_content,
            site = site,
            case_id = case_id, 
            email_content = email_content)
        error = None
        error_detail = None
        status = 200
        return_output = {
            "status": status,
            "message": "Success",
            "output": output
        }

    except openai.BadRequestError as e:
        status = 200
        summary_ = Api1.get_summary()
        start_time_ts = Api1.get_start_t()
        lang = Api1.get_lang()
        product_line = Api1.get_product_line()
        output = {
            "case_id": case_id,
            "gpt_extract":{
                "user_summary": summary_,
                "type": 'unclear_description',
                "email_split_sentence": []
            }, 
            "check_info":{
                "start_time_ts": start_time_ts,
                "end_time_ts": int(time.time()),
                "lang": lang,
                "product_line": product_line,
                "email_split_info":[]
            }
        }
        error = {"error": str(e)}
        tb = traceback.format_exc()
        error_detail = {"traceback": tb}
        return_output = {
            "status": status,
            "message": "Success", 
            "output": output
        }
    except KeyError as e:
        status = 400
        output = None
        error = {"error": str(e)}
        tb = traceback.format_exc()
        error_detail = {"traceback": tb}
        print(f'-------- (api1) case_id:{case_id}--------')
        print(error)
        return_output = {
            "status": status,
            "message": e.args[0], 
            "output": output
        }
    except (TimeoutError, RuntimeError) as e:
        status = 400
        output = None
        error = {"error": str(e)}
        tb = traceback.format_exc()
        error_detail = {"traceback": tb}
        print(f'-------- (api1) case_id:{case_id}--------')
        print(error)
        return_output = {
            "status": status,
            "message": 'ERROR', 
            "output": output
        }
    except Exception as e:
        status = 400
        output = None
        error = 'ERROR'
        tb = traceback.format_exc()
        error_detail =  {"error": str(e), "traceback": tb}
        print(f'-------- (api1) case_id:{case_id}--------')
        print(error_detail)
        return_output = {
            "status": status,
            "message": error, 
            "output": output
        }
    finally:
        logs = Api1.request_logs.get()
        generated_check_info_error_log = Api1.generated_check_info_error_log

        try:
            debug_data = {
                "status": status,
                "error_message": error,
                "error_detail": error_detail,
                "performance_t": Api1.txt_,
                "api_call_info": api_log}
        except:
            debug_data = {
                    "status": status,
                    "error_message": error,
                    "error_detail": {
                        "error detail" :error_detail,
                        "generated_check_info_error_log": generated_check_info_error_log
                    },
                    "performance_t": Api1.txt_,
                    "api_call_info": logs}

        write_cosmosDB(
            _id = _id,
            case_id = case_id, 
            input_data = input_data, 
            output_data = output,
            debug_data = debug_data)
        # await close_client_http()
    return return_output


# 測試
if __name__ == '__main__':
    from api1_v3.get_translate import initialize_google_translate
    initialize_google_translate()
    case_id= 'A2009150609-0019'
    email= 'cortez.jamessed12@gmail.com'
    phone= '09950920734'
    case_date= '1712038385'
    site= 'tw'
    product_type= 'Peripherals & Accessories'
    email_content= '''Apply Date: 2023/08/15 06:33:32.399 (UTC Time)<br><br>[聯絡資訊]<br>姓名: 許 郡軒<br>郵件信箱: junxuanxu@gmail.com<br>最近的服務據點: 臺灣 TAIWAN,R.O.C.<br>電話號碼: 0<br><br>[產品資訊]<br>產品類型: Peripherals & Accessories<br>產品型號: TUF-GAMING-750G<br>產品序號: R2YEOK00D3537U6<br>作業系統&韌體/BIOS版本: 電玩供應器沒反應<br><br>[詢問問題描述]<br>主旨: 電源供應器沒反應<br />電源供應器沒反應'''
    product_model= 'ROG Phone 3 (ZS661KS)'
    product_sn= 'L7AIGF0070645HD'
    problem_description_content= '''主旨: 電源供應器沒反應<br />電源供應器沒反應'''

    _id = 'test123'
    start_time = time.time()
    aa = asyncio.run(email_detect(_id, case_id, 
                                    email,phone, 
                                    case_date,
                                    site,
                                    product_type, 
                                    email_content,
                                    product_model, 
                                    product_sn,
                                    problem_description_content))
    print(json.dumps(aa, indent=2, ensure_ascii=False))
    print("DONE",time.time()-start_time)


    # test_ls = []
    # for i in range(10):
    #     start_time = time.time()
    #     asyncio.run(email_detect(case_id, 
    #                                 email,phone, 
    #                                 case_date,
    #                                 site,
    #                                 product_type, 
    #                                 email_content,
    #                                 product_model, 
    #                                 product_sn,
    #                                 problem_description_content, 
    #                                 mapping_table = KB_mappings))
        
    #     print("---------DONE", i, time.time()-start_time)
    #     test_ls.append(time.time()-start_time)
    # print(test_ls)
    
