# -*- coding: utf-8 -*-
import json
try:
    from .call_gemini import call_gemini as call_gpt
except ImportError:
    from call_gemini import call_gemini as call_gpt


def summary_prompt(email_context):
    sys_prompt = '''
Your objective is to summarize customers' inquiries. Below are some guidelines to follow:
1.Start by identifying the language used by the **CUSTOMERS FOR WRITING**, and use it as the summarized_in_this_language.(formatted as "xx-xx" e.g., "en-us" for American English)
2.Highlight specific segments pertinent to product issues, such as cases where notebooks fail to power on or display a blue screen.
3.Concisely summarize customers' inquiries using the language specified by summarized_in_this_language.
4.Avoid verbose, word-for-word descriptions.
5.Begin each summary with 'I' or 'My product' as the subject in the summarized_in_this_language.
6.Provide responses in JSON format.
7.If the content under [Problem Description] is too fragmented to extract meaningful sentences, return the original text as is in a single paragraph without breaking it down.

Example1:
email :"[Product Information]
Product Type: Premium PhoneProduct 

[Problem Description]
主旨: Overheating and Repair Inquiry
Hello ASUS Customer Service,
My ROG 3 tends to overheat after short usage and getting a CPU fan error message. I have been requesting the team to thoroughly check every part of my system for several months now. It is frustrating to have spent a significant amount of money on a system that is constantly crashing and hanging. I believe that with the specifications it has, these problems should not be occurring. I kindly request that my system be picked up and thoroughly checked for any issues with each and every part.
Thank you."
JSON format :{"summarize_in_this_language":"en-us","email_summary":"My ROG Phone 3 gets really hot after using it for a while and getting a CPU fan error message."}

Example2:
email :"[Product Information]
Product Type: 筆電

[Problem Description]
ប្រធាន: 我的電腦不能充電，可以怎麼辦?
另外我中文不太好，可以用英文回信給我嗎?"
JSON format :{"summarize_in_this_language":"zh-tw","email_summary":"我的電腦不能充電，用英文回信給我"}

Example3:
email :"Apply Date: 2024/09/25 20:22:08.698 (UTC Time)<br><br>[Información de contacto]<br>Apellido: Jorge Vasquez<br>Dirección de correo electrónico: shoxo94@gmail.com<br>Servicio técnico más cercano: Chile<br>Número de teléfono: 0<br><br>[Información de producto]<br>Tipo de producto: Gaming NB<br>Modelo de producto: FA617NT<br>Número de serie del producto: RANRKD006858413<br>Sistema operativo / firmware o versión del BIOS: Windows 11<br><br>[Descripción del problema]<br>please tell me ノートパソコンの画面が真っ暗になり、電源が入らなくなった場合はどうすればよいですか?"
JSON format :{"summarize_in_this_language":"ja-jp","email_summary":"ノートパソコンの画面が真っ暗で電源が入りません"}
'''
    user_prompt = f'''Kindly provide me with the 'summarize_in_this_language' and 'email_summary', and reply the language specified in 'summarize_in_this_language' for the output.
email:{email_context}
JSON format:'''
    return sys_prompt, user_prompt


async def summary_(
        input, 
        last_gpt = 'empty input', # 有測試到bug 不知道為什麼gpt可以正常回應 但回應的內容是None 所以預設None的話 即使跑第二次 也還是會像是第一次的結果
        error_message = None
        ):
    sys_prompt, user_prompt = summary_prompt(email_context = input)

    if last_gpt == 'empty input' :
        conversation = [
        {'role':'system','content':sys_prompt},
        {"role": "user", "content":user_prompt}
        ]
    else:
        if last_gpt == None:
            last_gpt = 'None'
        conversation = [
        {'role':'system','content':sys_prompt},
        {"role": "user", "content":user_prompt}, 
        {"role": "assistant", "content":last_gpt}, 
        {"role": "user", "content":f'''Error message is : {error_message}. Please correct and try again.'''}
        ]
    ans = await call_gpt(conversation)
    return ans


async def gpt_summary(input):
    gpt_response = await summary_(input = input)
    try:
        gpt_response_json = json.loads(gpt_response)
        ans_sum = gpt_response_json['email_summary']
        ans_lan = gpt_response_json['summarize_in_this_language']
        return ans_sum, ans_lan, gpt_response
    except:
        try:
            gpt_response = gpt_response.replace("\\", " ")
            gpt_response = gpt_response.replace('```', '')
            gpt_response = gpt_response.replace('json', '')
            gpt_response_json = json.loads(gpt_response)
            ans_sum = gpt_response_json['email_summary']
            ans_lan = gpt_response_json['summarize_in_this_language']
            return ans_sum, ans_lan, gpt_response
        except Exception as e:  # 第一次失敗 重試一次
            gpt_response_retry = await summary_(
                input = input, 
                last_gpt = gpt_response,
                error_message = e,)
            try:
                gpt_response_json = json.loads(gpt_response_retry)
                ans_sum = gpt_response_json['email_summary']
                ans_lan = gpt_response_json['summarize_in_this_language']
                return ans_sum, ans_lan, gpt_response_retry
            except:
                try:
                    gpt_response_retry = gpt_response_retry.replace("\\", " ")
                    gpt_response_retry = gpt_response_retry.replace('```', '')
                    gpt_response_retry = gpt_response_retry.replace('json', '')
                    gpt_response_json = json.loads(gpt_response)
                    ans_sum = gpt_response_json['email_summary']
                    ans_lan = gpt_response_json['summarize_in_this_language']
                    return ans_sum, ans_lan, gpt_response_retry
                except Exception as e: # 第二次失敗 放棄
                    raise TimeoutError(f'error in gpt_summary:{e}, input:{input}')


if __name__ == '__main__':
    import asyncio
    input='''[Product Information]\nProduct Type: GAMING HANDHELDS\n\n[Problem Description]\nSubject: RogAllyX windows and trigger<br />Hello,<br /><br />My partner and I each have a ROG ALLY X.<br /><br />However, my partner's is STILL stuck at 100% and won't return to normal.<br /><br />He spends his nights waiting sometimes, but this is too much at €900/unit...<br /><br />Furthermore, his right trigger makes a strange noise, like a spring, while the left one, on my console, doesn't'''
    aa = asyncio.run(gpt_summary(input))
    print(aa)


