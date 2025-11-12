import json
try:
    from .call_gpt import call_gpt4o as call_gpt
except ImportError:
    from call_gpt import call_gpt4o as call_gpt

def split_prompt(email_context, lang):
    sys_prompt = '''
You are an intelligent assistant whose task is to extract structured product-related information from customer emails. Your goal is to decompose the customer's message into standalone, self-contained sentences that clearly describe individual product issues or inquiries.

## Extraction Rules:
1. Write all extracted sentences in the language specified by the user in `{lang}`.
2. Output the result in a JSON object with keys formatted as `"extracted_sentenceN"` (e.g., `"extracted_sentence1"`, `"extracted_sentence2"`, ...).

---
## Extraction Priority
Always extract the following categories, even in long emails. Each item must be separated into clear, standalone sentences:

### High-Priority Categories:
- **Technical Support**  
  Product issues involving hardware/software, performance, drivers, power, charging, connectivity, display, BIOS, keyboard, etc.
- **Repair Consultation**  
  Service center lookup, repair status, repair applications, quotations, and complaints.
- **Warranty-Related**  
  Warranty policy, purchasing extended warranty, checking or updating warranty period.

---

## Sentence Structuring Rules

3. Each extracted sentence must be:
  - Self-contained and interpretable alone  
  - Include relevant product context if available  
  - Written in the specified output language (`{lang}`)

4. When multiple statements describe the same issue progression (e.g., symptom + attempted solution + result), merge them into a single, fluent sentence:

  Example (merge):  
  "いくつかのアプリが正常に動作しなくなり、再起動しても状況が変わらない状態です。"  
  Don't extract separately:  
  "幾つかのアプリが正常に動作しなくなっています。"  
  "再起動しても状況は変わりません。"

5. Do not split phrases that are:
  - Part of a cause-effect explanation  
  - Attempted solution followed by failure  
  - Symptom escalation

6. **Always speak from the customer's perspective.**  
   - Do **not** use third-person narration like `"The customer said..."` or `"The user wants..."`  
   - Use phrasing that reflects direct experience or intent  
     Examples:  
     `"Had the screen replaced at an ASUS center."`  
     `"Need to check warranty on the new display."`  
     `"Noticed the battery drains fast after the last update."`  
     Avoid:  
     `"The customer had their screen replaced..."`  
     `"The user is asking about..."`

---
## Sentence Simplification (Optional Refinement Phase)

7. After extraction, simplify and shorten the sentence when possible to make it more conversational and concise — **as long as the sentence remains self-contained and retains necessary product context**. Use everyday language where appropriate. Do not reduce clarity or introduce ambiguity.

Examples:
- Input: `I recently had the display of my ASUS TUF laptop replaced at an ASUS-authorized service center.`  
  Output: `My Gaming NB had the display replaced at an ASUS-authorized service center.`

- Input: `Although my laptop itself is out of warranty, I would like to confirm the warranty duration that applies to the newly replaced display.`  
  Output: `I need to confirm the warranty duration for the newly replaced display.`

---
## Trimming Strategy for Long Emails

8. If the email content would result in more than 5 extracted sentences:

  - Only retain sentences related to the high-priority categories above  
  - Among these, prefer descriptive and diagnostic statements (e.g., `"Windows reports code 43 with the GPU"`)
  - Omit customer self-action statements (e.g., `"I checked all drivers but none worked"`)

---

## Input Format:

The email context: `{email_context}`  
Provide the response in `"{lang}"` and structure it in JSON format as follows:

```json
{
  "extracted_sentence1": "...",
  "extracted_sentence2": "...",
  ...
}
'''
    user_prompt = f'''
The email context:{email_context}.
Provide the response in "{lang}"  and structure it in JSON format as described.'''
    return sys_prompt, user_prompt

async def gpt_split(email_content_input, lang):
    sys_prompt, user_prompt = split_prompt(email_context = email_content_input, lang = lang)
    conversation = [
        {'role':'system','content':sys_prompt},
        {"role": "user", "content":user_prompt}
        ]
    gpt_response = await call_gpt(conversation)
    try:
        if gpt_response == None:
            raise ValueError('gpt_response is None')
        json.loads(gpt_response)
    except:
        gpt_response = await call_gpt(conversation)
    return gpt_response
        


### 測試 ###
if __name__ == '__main__':
    import asyncio
    input_ = '''Apply Date: 2025/02/23 09:20:50.280 (UTC Time)<br><br>[Fornitore/numero del processore della CPU]<br>名:  gnome<br>メールアドレス: 19830526kenjam@gmail.com<br>現在お住まいの国: Japan<br>電話番号: 0<br><br>[製品情報]<br>製品タイプ: ASUS NUC DISTRIBUTION<br>製品モデル: NUC12SNKI7<br>製品シリアル番号: S4ABMF027263NBV<br>オペレーションシステム/ファームウェアまたはBIOSバージョン: 0054<br><br>[問題点説明]<br>件名: BIOSアップデートできない<br />このPCのダウンロードリストから0061をダウンロードインストールした後BIOSを開いても0054のまま変わらず、無料のPCの状態を調べれるものでリサーチしたらBIOS0061になっていたのに実際適応されていないという状況です。ドライバもダウンロードインストールをしても状態が変わらないという現象が続いています。どこに問題があるのかわからないです。<br />そもそもこのPCがthunderboltドライバがインストール出来て正常に使えるタイプのものかどうかを調べていただきたいです。<br />Amazonで購入しましたが、販売ページには販売元サポートとASUSサポート両方受けられるとのことでしたが、販売元からのメールが返信来なくなっています。現在４日目。このPCは企業向けタイプとのことですが、個人に販売してもよいモデルなのでしょうか？販売元の対応が悪いので不信感でいっぱいです。<br />返品可能時間内なので、個人向けに販売できる正規品なのかどうかをまず教えていただけると助かります。'''
    print(asyncio.run(gpt_split(email_content_input = input_, lang='ja-jp')))

# # 測試
# input = '''
# '[Product Information]\nProduct Type: Gaming NB\n\n[Problem Description]\n件名: Bit lockerの解除について\n電源をつけた所、bit lockerの入力を求められました。\n\nしかし、キーが分からずどうすればよいでしょうか'
# '''
# await gpt_split(input, lang='ja-jp')
