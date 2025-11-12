# 更新 'rag' 欄位來包含換行符號和 URL
import pandas as pd

def remove_contact_sentence(text):
    lines = text.split('\n')
    if "contact asus customer service" in lines[-1].lower():
        lines = lines[:-1]
    return '\n'.join(lines)


# def append_url_with_newline(row):
#     base_url_front = "https://www.asus.com/"
#     base_url_behide = "/support/faq/"
#     site = row['site']
#     kb_number = row['kb_no']
#     url = f"{base_url_front}{site}{base_url_behide}{kb_number}/"
#     # first_sentence = row['first_sentence']
#     # close_sentence = row['close_sentence']
#     return f"{row['first_sentence']}\n{row['rag_draft']}\n\n{row['close_sentence']}\n{row['title']}: {url}"  # 在 'rag' 內容後添加換行符號和 URL


def append_url_with_newline(row):
    base_url_front = "https://www.asus.com/"
    base_url_behide = "/support/faq/"
    
    if isinstance(row, (dict, pd.Series)):
        # 如果 row 是字典或 Series，按原來的方式處理
        # site = row['site'] 
        # site_replaced = row['site_replaced'] 
        # 指定繁中使用 hk, 簡中使用 cn 9/6
        if row['site_replaced'] == 'tw':
            site_replaced = 'hk'
        else:
            site_replaced = row['site_replaced']
        kb_number = row['kb_no']
        url = f"{base_url_front}{site_replaced}{base_url_behide}{kb_number}/"
        return f"{row['first_sentence']}\n{row['rag_draft']}\n\n{row['close_sentence']}\n{row['title']}: {url}"
    elif isinstance(row, str):
        # 如果 row 是字符串，我們需要以不同的方式處理
        # 這裡需要根據實際情況來決定如何處理字符串
        # 例如，我們可以簡單地返回這個字符串，或者進行一些其他處理
        return row
    else:
        # 如果 row 既不是字典/Series 也不是字符串，拋出一個錯誤
        raise TypeError(f"Unexpected type for row: {type(row)}")


def append_url_with_newline_global(row):
    base_url = "https://www.asus.com/support/faq/"
    
    if isinstance(row, (dict, pd.Series)):
        kb_number = row['kb_no']
        url = f"{base_url}{kb_number}/"
        return f"{row['first_sentence']}\n{row['rag_draft']}\n\n{row['close_sentence']}\n{row['title']}: {url}"
    elif isinstance(row, str):
        return row
    else:
        raise TypeError(f"Unexpected type for row: {type(row)}")


# 舊版
# def append_url_with_newline(row):
#     base_url_front = "https://www.asus.com/"
#     base_url_behide = "/support/faq/"
#     site = row['site']
#     kb_number = row['kb_no']
#     url = f"{base_url_front}{site}{base_url_behide}{kb_number}/"
#     # return f"{row['rag']}\n\n {row['title']}\n {url}"  # 在 'rag' 內容後添加換行符號和 URL
#     return f"{row['rag']}\n {row['title']}: {url}"  # 在 'rag' 內容後添加換行符號和 URL
