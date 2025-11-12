import time
from openai import AsyncAzureOpenAI
import os
import textwrap
# import config

RESOURCE_ENDPOINT_ : str = os.getenv('MYAPP_GPT41MINI_RESOURCE_ENDPOINT')# type: ignore[assignment]
API_KEY_ = os.getenv('MYAPP_GPT41MINI_API_KEY')
intentDetect_ : str = os.getenv('MYAPP_GPT41MINI_INTENTDETECT')# type: ignore[assignment]
if RESOURCE_ENDPOINT_ is None or API_KEY_ is None or intentDetect_ is None:
    raise ValueError("Environment variables MYAPP_GPT41MINI_API_KEY, MYAPP_GPT41MINI_RESOURCE_ENDPOINT, and MYAPP_GPT41MINI_INTENTDETECT must be set.")

client = AsyncAzureOpenAI(
    azure_endpoint = RESOURCE_ENDPOINT_,
    api_key = API_KEY_,
    api_version = "2025-01-01-preview"
)


async def reply_with_faq(content, question, email_lang, product_type):

    system_content = textwrap.dedent(f'''
    You are a customer service robot programmed to address inquiries within a specific framework. Please follow these guidelines strictly :
    #0. Please ensure your responses are professional and **only in language {email_lang}** (avoiding 'Simplified Chinese').
    #1. Confine your responses strictly within the parameters of the provided information. Do not offer answers or insights beyond this scope.
    #2. Uphold a professional customer service tone at all times, avoid excessive redundancy, and limit responses to 150 words.
    #3. Thoroughly answer questions using only the information given, without indicating that the answers are based on a particular source or article.
    #4. Adapt your responses to match the language of the user’s question, specifically using 'Traditional Chinese' when requested.
    #5. Generate answer must be down to the smallest detail and make sure user's question can be completed by answer.
    #6. Do not provide any url link or relevant articles.
    #7. Don’t answer directly based on the product examples in the article, you must emphasize the method.
    #8. Forbidden for displaying "please contact ASUS customer service center for further assistance" and other similar statements in the generated content.
    #9. Do not ask user for more information. Answer thoroughly based on the given information.
    #10. Reply based on the {content} only. Do not provide any information beyond what is in the content.
    #11. If the {question} contains any warranty-related issues, please remove the warranty questions and keep only the non-warranty questions.
         For example:
         Input: “My notebook's warranty ends in June and I want to modify it, the fingerprint sensor is not available and I cannot activate it.”
         Output: “I want to modify my notebook, the fingerprint sensor is not available and I cannot activate it.”
    #12. Please provide solutions directly from {content} for the non-warranty questions in your response.
    #13. Please strictly prohibited to repeat the questions from {question} in your response.
    #14. Please respond based on {question} and {product_type}, and provide an appropriate solution by referencing {content}. 
    The following is the information at your disposal:''') + product_type + content

    user_content = textwrap.dedent(f'''Please ensure your responses are professional and in language: " + email_lang + "(avoiding 'Simplified Chinese'). and reply in numbered bullet points (1, 2, 3, ...).:''') + question
    conversation = [
    {"role": "system", "content": system_content},
    {"role": "user", "content": user_content},
    {"role": "assistant", "content": textwrap.dedent(f'''Understood. I will respond in language: {email_lang }(avoiding 'Simplified Chinese') and strictly follow the guidelines. I will generate a solution in numbered bullet points (1, 2, 3, ...), using **only plain text format**. I am strictly forbidden from using Markdown syntax, including `**bold**`, `_italic_`, `~strikethrough~`, or any other special formatting. I will only use plain text for responses.''')}
    ]

    try:
        response = await client.chat.completions.create(
            model=intentDetect_,
            messages=conversation,
            max_tokens=1000,
            n=1,
            stop=['}','User:'],
            temperature=0
            )
        generated_response = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
    except:
        # time.sleep(120)
        time.sleep(3)
        response = await client.chat.completions.create(
            model=intentDetect_,
            messages=conversation,
            max_tokens=1000,
            n=1,
            stop=['}','User:'],
            temperature=0
            )
        generated_response = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
    print(generated_response)
    return generated_response


async def summarize_question(question, summary, email_lang, product_type):
    
    # # original conversation for gpt35、gpt4o
    # conversation = [
    # {"role": "system", "content": textwrap.dedent(f'''You are an AI assistant who briefly describes the problems and provides solution titles in the specified language.''')},
    # {"role": "user", "content": textwrap.dedent(f'''Briefly describe the problem, generate a solution title in {lang}. The entire sentence should be in {lang} and follow this structure: 'To address [solve/handle the problem] issue, please consider the following troubleshooting steps:'. For example, if the input is 'My laptop won't turn on. What should I do?' and the language is en-us, the output should be 'To address a laptop that won't turn on issue, please consider the following troubleshooting steps:'. Only provide the solution title, nothing else.''')},
    # {"role": "assistant", "content": textwrap.dedent(f'''Understood. I will generate a solution title based on the problem description provided and the specified language: {lang}. The entire sentence will be in {lang} and follow the structure 'The method to [solve/handle the problem] is as follows:'.''')},
    # {"role": "user", "content": textwrap.dedent(f'''Problem description: {question}''')}
    # ]

    # gpt4omini_jp
    conversation = [
    {"role": "system", "content": textwrap.dedent(f"""
        You are an AI assistant who briefly describes the problems and provides solution titles in the specified language. Please follow these guidelines strictly :
        1. Please ensure your responses are professional and only in language {email_lang}.   
        2. When summarizing, do not use personal pronouns such as "I" or "you". Summaries should be neutral and objective.
        3. If the {question} mentions any WARRANTY issues, please ignore the warranty-related parts and do not answer them, but still respond to any other questions that are not related to warranty.                                                   
        """)},
    {"role": "user", "content": textwrap.dedent(f"""
        Briefly describe the problem, generate a solution title in {email_lang}. The entire sentence should be in {email_lang} and follow this structure: 
        'To address [solve/handle the problem] issue, please consider the following troubleshooting steps:'. 
        
        Examples:
        Example#1, if the input is 'My laptop won't turn on. What should I do?' and the language is en-us, 
        the output should be 'To address a laptop that won't turn on issue, please consider the following troubleshooting steps:'.

        Example#2, if the input is 'After updating the firmware of my LCD monitor to MCM108, it was working without any issues.' and the language is jp-jp, 
        the output should be 'LCDモニターのファームウェアをMCM108に更新後の動作確認問題に対処するため、以下のトラブルシューティング手順をご検討ください。'.

        Example#3, if the input is 'How to disable Modern Standby (S0 mode)' and the language is ko-kr, 
        the output should be 'Modern Standby(S0 모드) 비활성화 문제를 해결하기 위해 다음과 같은 문제 해결 단계를 고려해 주세요.'.

        Example#4, if the input is 'The SSD is not detected or does not appear as an option in the installation location selection window' and the language is ro-ro, 
        the output should be 'Pentru a rezolva problema SSD-ului care nu este detectat sau nu apare ca opțiune în fereastra de selecție a locației de instalare, vă rugăm să luați în considerare următorii pași de depanare:'.

        Example#5, if the input is 'My desktop cannot be turned on by pressing the power button, it is connected to the power cord but there is no response. How much does it cost to replace the motherboard' and the language is zh-hant, 
        the output should be '為了解決桌上型電腦按下電源按鈕無法開機的問題，請考慮以下故障排除步驟：'. 

        Example#6, if the input is 'My notebook's warranty ends in June and I want to modify it, the fingerprint sensor is not available and I cannot activate it' and the language is ar-eg, 
        the output should be 'لمعالجة مشكلة عدم تفعيل مستشعر البصمة في اللابتوب بعد انتهاء الضمان في يونيو، يرجى اتباع خطوات استكشاف الأخطاء التالية:'. 

        Example#7, if the input is 'My notebook's warranty ends in June and I want to modify it, the fingerprint sensor is not available and I cannot activate it' and the language is he-il, 
        the output should be 'כדי לטפל בבעיה של אי הפעלת חיישן טביעת האצבע במחשב הנייד לאחר תום האחריות ביוני, אנא שקלו את שלבי פתרון הבעיות הבאים:'.

        Only provide the solution title, nothing else.
        Problem description: {question} {product_type}            
        """)}
    ]   

    try:
        response = await client.chat.completions.create(
            model=intentDetect_,
            messages=conversation,
            max_tokens=1000,
            n=1,
            stop=['}','User:'],
            temperature=0
            )
        generated_response = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
    except:
        # time.sleep(120)
        time.sleep(3)
        response = await client.chat.completions.create(
            model=intentDetect_,
            messages=conversation,
            max_tokens=1000,
            n=1,
            stop=['}','User:'],
            temperature=0
            )
        generated_response = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
    # print(generated_response)
    return generated_response


async def translate_text(lang):
    
    user_content = textwrap.dedent(f'''Translate the following English text to {lang}: "Kindly refer to the below link for more troubleshooting details"
                        Provide only the translated text without any explanations or additional content.''')

    conversation = [
        {"role": "system", "content": textwrap.dedent(f'''You are a professional translator.''')},
        {"role": "user", "content": user_content}
    ]


    try:
        response = await client.chat.completions.create(
            model=intentDetect_,
            messages=conversation,
            max_tokens=1000,
            n=1,
            stop=['}','User:'],
            temperature=0
            )
        generated_response = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
    except:
        # time.sleep(120)
        time.sleep(3)
        response = await client.chat.completions.create(
            model=intentDetect_,
            messages=conversation,
            max_tokens=1000,
            n=1,
            stop=['}','User:'],
            temperature=0
            )
        generated_response = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
    # print(generated_response)
    return generated_response



# # reply_with_faq 測試範例
# if __name__ == '__main__':
#     import asyncio

#     content = '''
#                 ---

#                 Applicable Products: Notebook, Desktop, All-in-One PC, Gaming handheld, MiniPC, Wireless Router, Optical Storage, NUC

#                 If you have driver update requests on your device, we preferentially suggest you get the updates from MyASUS or ASUS official website.

#                 With ASUS verified drivers, it can ensure your device is running with the best and most compatible performance.

#                 If you have trouble on installing drivers, please refer to How to uninstall drivers.

#                 To provide you more detailed instruction, you can also click ASUS YouTube video link below to know more about How to Search and Download Drivers, Utilities, BIOS and User Manuals.
#                 [https://www.youtube.com/watch?v=04QSvd\_X3ZI](https://www.youtube.com/watch?v=04QSvd_X3ZI)

#                 You can download Drivers, Utilities, BIOS, and User Manuals from MyASUS or from ASUS official site. Please refer to the following three methods to download the files:

#                 Method 1: Search and download Drivers, Utilities, BIOS, and User Manuals via MyASUS

#                 1. Type and search \[MyASUS] in the Windows search bar ①, then click \[Open]②. (The left-side search illustration below is in Windows 11, and the right-side is in Windows 10.)
#                 Note: If there is no result searched, it means your device may not install it, and please refer to How to install MyASUS.
#                 2. Please refer to the downloading methods below based on what you want to download:

#                 Download and Install Drivers, Utilities, and BIOS in MyASUS

#                 1. In the MyASUS window, click \[System Update]①.
#                 Note: If your device does not display the System Update tab, it means your device does not support this feature. You can use Method 2: Download the file from ASUS official site. Learn more about Why can I only see the partial features in the MyASUS app.
#                 2. When entering the System Update page, MyASUS will automatically check and list the items that need updating for your system.
#                 Note: If no update items are displayed on this page, it means your system is already up to date.
#                 3. Check the items you want to update②, then click \[Update Selected Items]③.
#                 4. MyASUS will automatically start downloading and installing the selected items.
#                 5. After installation, you can check whether the selected items were successfully updated in \[Update history]④.

#                 Download User Manuals in MyASUS

#                 1. In the MyASUS window, click \[Customer Support]①.
#                 2. On the \[FAQ] page②, click \[Computer related]③.
#                 3. Choose any problem category and description④, then click \[Search]⑤.
#                 4. After the search results appear, click \[For more information, refer to the device user manual]⑥ at the bottom of the support article, and MyASUS will redirect you to the download site for the user manual of your product model.

#                 Method 2: Search and download Drivers, Utilities, BIOS, and User Manuals from ASUS official site

#                 1. Please go to the ASUS support site, and then enter Model Name in the search bar and press the Enter key on the keyboard①. Here you can learn more about How to check the model name. (The following takes UX482EA model as a reference.)
#                 2. After the search result shows up, please select the \[Support] category② and then select \[Driver & Tools]③.
#                 3. Enter the product support site, you can download drivers, utilities, BIOS, and user manuals here.
#                 4. Please refer to the downloading methods below based on what you want to download:

#                 Download Driver and Utility

#                 1. On the product support site, select \[Driver & Utility] tab①, and then select \[Driver & Tools] category②.
#                 2. Please select the Model Name③. Here you can learn more about How to check the model name, to choose the correct model name.
#                 Note: Some models may not have this option, please continue to the next step.
#                 3. Scroll down the menu to choose the Operating System version you use④.
#                 Note: ASUS only provides drivers and utilities for supported operating systems. If you are using a different operating system, please make sure to obtain drivers from other sources or get similar drivers from devices of the same model.
#                 4. You will see the list of drivers and utilities on the product support site. Find the file you want to download, then click the \[Download] behind the file to download it⑤.
#                 If you want to see all versions of some category, please click \[Show all] under this category. If you want to see all drivers and utilities, you can click \[EXPAND ALL].

#                 Download BIOS

#                 1. On the product support site, select \[Driver & Utility] tab①, and then select \[BIOS & FIRMWARE] category②.
#                 2. Please select the Model Name③. Here you can learn more about How to check the model name, to choose the correct model name.
#                 Note: Some models may not have this option, please continue to the next step.
#                 3. You will see the list of BIOS on the product support site. Find the file you want to download, and then click the \[Download] behind the file to download it④.
#                 If you want to see all versions of some category, please click \[Show all] under this category. If you want to see all BIOS, you can click \[EXPAND ALL].

#                 Download User Manual

#                 1. On the product support site, select \[Manual & Document] tab①, and then select \[Manual] category②.
#                 2. You will see the list of User Manual on the product support site. Find the file you want to download, and then click the \[Download] behind the file to download it③.

#                 Method 3: One-Click Update Drivers from the ASUS official site

#                 Applicable Products: Notebook, Desktop, All-in-One PCs, Gaming Handheld

#                 System Requirements: Devices that support and have installed the ASUS System Control Interface driver. Learn more about How to download and install the ASUS System Control Interface driver.

#                 One-Click Update drivers helps you automatically check and list versions newer than those on your system. If your device supports this feature, please follow these steps:

#                 1. First, visit the ASUS support site, enter your product model name in the search bar, and press Enter on the keyboard①. Learn more about How to find the model name of your device. (The following steps use the UX581LV model as an example)
#                 2. After the search results appear, select the \[Support] category② and then click \[Driver & Tools]③.
#                 3. Click \[One-click driver download]④ to begin checking if newer versions are available for installation compared to those on your system.
#                 Note: If the 「One-click driver download」 option does not appear on your product support page, it means this model does not support this feature.
#                 After clicking 「One-click driver download」, if the following screen appears, it means your device lacks the necessary components to perform the quick update. Please click \[Download] and install it first. Once the installation is complete, return to the product support page to continue using the one-click update feature.

#                 Note: To learn how to install the ASUS Support Agent, click here to expand the detailed steps.

#                 A. After downloading the ASUS Support Agent file, right-click on the compressed folder①, and select \[Extract All]②.
#                 B. Click \[Extract]③.
#                 C. After extraction is complete, double-click the application to start the installation process④.
#                 D. If the User Account Control window appears, select \[Yes]⑤.
#                 E. Choose your preferred language for the installer⑥, and click \[Install]⑦.
#                 F. The ASUS Support Agent is installing, please wait for the installation to complete.
#                 G. Once the ASUS Support Agent installation is complete, click \[Close and proceed to ASUS Support site]⑧ to continue using the 「One-click driver download」 feature.

#                 4. Please read the ASUS privacy policy. After confirming, check the box \[I Agree]⑤ and click \[Start]⑥.
#                 5. Please read the precautions. Ensure the power cord is connected and the network connection is stable, then click \[Yes]⑦.
#                 6. After the webpage completes the detection, it will list the items that can be updated. Check the items you wish to update⑧ and click \[Download and install]⑨.
#                 Software updates generally help with system stability and optimization, so it is recommended to frequently check if your device is using the latest version.
#                 7. Click \[Yes]⑩ to begin the download and installation.
#                 8. The webpage is downloading and installing, please wait for the installation to complete.
#                 Note: During the installation process, ensure the device is plugged in and do not force shutdown or close the browser to ensure proper installation.
#                 9. After installation is complete, some drivers may require you to restart your device to complete the setup. Click \[Restart now]⑪.
#                 Note: Before restarting the device, make sure to save your data to avoid data loss.

#                 ---
                    
#                 '''
#     question = "I get a message on my mobile that says 'could not connect new device' and a message on my computer that says 'Driver error' "
#     email_lang='sv-se'
#     productType = 'Wireless'

#     asyncio.run(reply_with_faq(content = content, question = question, email_lang=email_lang, productType=productType))


# summarize_question 測試範例
if __name__ == '__main__':
    import asyncio

    content = content = '''
                ---

                Applicable Products: Notebook, Desktop, All-in-One PC, Gaming handheld, MiniPC, Wireless Router, Optical Storage, NUC

                If you have driver update requests on your device, we preferentially suggest you get the updates from MyASUS or ASUS official website.

                With ASUS verified drivers, it can ensure your device is running with the best and most compatible performance.

                If you have trouble on installing drivers, please refer to How to uninstall drivers.

                To provide you more detailed instruction, you can also click ASUS YouTube video link below to know more about How to Search and Download Drivers, Utilities, BIOS and User Manuals.
                [https://www.youtube.com/watch?v=04QSvd\_X3ZI](https://www.youtube.com/watch?v=04QSvd_X3ZI)

                You can download Drivers, Utilities, BIOS, and User Manuals from MyASUS or from ASUS official site. Please refer to the following three methods to download the files:

                Method 1: Search and download Drivers, Utilities, BIOS, and User Manuals via MyASUS

                1. Type and search \[MyASUS] in the Windows search bar ①, then click \[Open]②. (The left-side search illustration below is in Windows 11, and the right-side is in Windows 10.)
                Note: If there is no result searched, it means your device may not install it, and please refer to How to install MyASUS.
                2. Please refer to the downloading methods below based on what you want to download:

                Download and Install Drivers, Utilities, and BIOS in MyASUS

                1. In the MyASUS window, click \[System Update]①.
                Note: If your device does not display the System Update tab, it means your device does not support this feature. You can use Method 2: Download the file from ASUS official site. Learn more about Why can I only see the partial features in the MyASUS app.
                2. When entering the System Update page, MyASUS will automatically check and list the items that need updating for your system.
                Note: If no update items are displayed on this page, it means your system is already up to date.
                3. Check the items you want to update②, then click \[Update Selected Items]③.
                4. MyASUS will automatically start downloading and installing the selected items.
                5. After installation, you can check whether the selected items were successfully updated in \[Update history]④.

                Download User Manuals in MyASUS

                1. In the MyASUS window, click \[Customer Support]①.
                2. On the \[FAQ] page②, click \[Computer related]③.
                3. Choose any problem category and description④, then click \[Search]⑤.
                4. After the search results appear, click \[For more information, refer to the device user manual]⑥ at the bottom of the support article, and MyASUS will redirect you to the download site for the user manual of your product model.

                Method 2: Search and download Drivers, Utilities, BIOS, and User Manuals from ASUS official site

                1. Please go to the ASUS support site, and then enter Model Name in the search bar and press the Enter key on the keyboard①. Here you can learn more about How to check the model name. (The following takes UX482EA model as a reference.)
                2. After the search result shows up, please select the \[Support] category② and then select \[Driver & Tools]③.
                3. Enter the product support site, you can download drivers, utilities, BIOS, and user manuals here.
                4. Please refer to the downloading methods below based on what you want to download:

                Download Driver and Utility

                1. On the product support site, select \[Driver & Utility] tab①, and then select \[Driver & Tools] category②.
                2. Please select the Model Name③. Here you can learn more about How to check the model name, to choose the correct model name.
                Note: Some models may not have this option, please continue to the next step.
                3. Scroll down the menu to choose the Operating System version you use④.
                Note: ASUS only provides drivers and utilities for supported operating systems. If you are using a different operating system, please make sure to obtain drivers from other sources or get similar drivers from devices of the same model.
                4. You will see the list of drivers and utilities on the product support site. Find the file you want to download, then click the \[Download] behind the file to download it⑤.
                If you want to see all versions of some category, please click \[Show all] under this category. If you want to see all drivers and utilities, you can click \[EXPAND ALL].

                Download BIOS

                1. On the product support site, select \[Driver & Utility] tab①, and then select \[BIOS & FIRMWARE] category②.
                2. Please select the Model Name③. Here you can learn more about How to check the model name, to choose the correct model name.
                Note: Some models may not have this option, please continue to the next step.
                3. You will see the list of BIOS on the product support site. Find the file you want to download, and then click the \[Download] behind the file to download it④.
                If you want to see all versions of some category, please click \[Show all] under this category. If you want to see all BIOS, you can click \[EXPAND ALL].

                Download User Manual

                1. On the product support site, select \[Manual & Document] tab①, and then select \[Manual] category②.
                2. You will see the list of User Manual on the product support site. Find the file you want to download, and then click the \[Download] behind the file to download it③.

                Method 3: One-Click Update Drivers from the ASUS official site

                Applicable Products: Notebook, Desktop, All-in-One PCs, Gaming Handheld

                System Requirements: Devices that support and have installed the ASUS System Control Interface driver. Learn more about How to download and install the ASUS System Control Interface driver.

                One-Click Update drivers helps you automatically check and list versions newer than those on your system. If your device supports this feature, please follow these steps:

                1. First, visit the ASUS support site, enter your product model name in the search bar, and press Enter on the keyboard①. Learn more about How to find the model name of your device. (The following steps use the UX581LV model as an example)
                2. After the search results appear, select the \[Support] category② and then click \[Driver & Tools]③.
                3. Click \[One-click driver download]④ to begin checking if newer versions are available for installation compared to those on your system.
                Note: If the 「One-click driver download」 option does not appear on your product support page, it means this model does not support this feature.
                After clicking 「One-click driver download」, if the following screen appears, it means your device lacks the necessary components to perform the quick update. Please click \[Download] and install it first. Once the installation is complete, return to the product support page to continue using the one-click update feature.

                Note: To learn how to install the ASUS Support Agent, click here to expand the detailed steps.

                A. After downloading the ASUS Support Agent file, right-click on the compressed folder①, and select \[Extract All]②.
                B. Click \[Extract]③.
                C. After extraction is complete, double-click the application to start the installation process④.
                D. If the User Account Control window appears, select \[Yes]⑤.
                E. Choose your preferred language for the installer⑥, and click \[Install]⑦.
                F. The ASUS Support Agent is installing, please wait for the installation to complete.
                G. Once the ASUS Support Agent installation is complete, click \[Close and proceed to ASUS Support site]⑧ to continue using the 「One-click driver download」 feature.

                4. Please read the ASUS privacy policy. After confirming, check the box \[I Agree]⑤ and click \[Start]⑥.
                5. Please read the precautions. Ensure the power cord is connected and the network connection is stable, then click \[Yes]⑦.
                6. After the webpage completes the detection, it will list the items that can be updated. Check the items you wish to update⑧ and click \[Download and install]⑨.
                Software updates generally help with system stability and optimization, so it is recommended to frequently check if your device is using the latest version.
                7. Click \[Yes]⑩ to begin the download and installation.
                8. The webpage is downloading and installing, please wait for the installation to complete.
                Note: During the installation process, ensure the device is plugged in and do not force shutdown or close the browser to ensure proper installation.
                9. After installation is complete, some drivers may require you to restart your device to complete the setup. Click \[Restart now]⑪.
                Note: Before restarting the device, make sure to save your data to avoid data loss.

                ---
                    
                '''

    question = "I get a message on my mobile that says 'could not connect new device' and a message on my computer that says 'Driver error'"
    email_lang = 'sv-se'
    product_type = 'Wireless'

    result = asyncio.run(summarize_question(question = question, summary = content, email_lang=email_lang, product_type=product_type))
    print(result)


# # summarize_question 測試範例
# if __name__ == '__main__':
#     import asyncio

#     lang = 'en-us'
   
#     asyncio.run(translate_text(lang=lang))