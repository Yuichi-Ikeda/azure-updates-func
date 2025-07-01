import os
import logging
import openai
import requests
from datetime import datetime, timezone
from azure.communication.email import EmailClient

SYSTEM_PROMPT_TITLE = "入力された英文を日本語に翻訳して下さい。先頭のラベルは、次のように翻訳してください。General Availability: 一般提供：, Launched: 一般提供：, In preview: パブリックプレビュー：, Public Preview: パブリックプレビュー：, Private Preview: プライベートプレビュー：, Retirement: リタイアメント："
SYSTEM_PROMPT_DESCRIPTION = "HTML書式で入力された文書の一部を日本語に翻訳して下さい。文書は <div> タグで開始して、</div> タグで終了してください。文書中に lang='EN-US' の属性がある場合は lang='JA-JP' に変更してください。font-family: Arial; や font-family: Times New Roman; のような英文フォントの属性は font-family: Noto Sans JP; に変更してください。それ以外の style 属性やタグ記述は、既存のままオリジナルの HTML書式を保持してください。"

HTML_TEMPLATE = '''\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>Azure 更新情報</title>
  <style>
    body {{
      font-family: Noto Sans JP;
      font-size: 1.0em;    
      margin: 40px;
      background: #fff;
      color: #222;
    }}
    .content {{
      font-family: Noto Sans JP;
      font-size: 1.0em;    
      padding: 22px 28px;
      border-radius: 10px;
      box-shadow: 0 2px 8px #0001;
      margin-bottom: 32px;
    }}
    .title {{
      background: #f9f9fb;    
      font-family: Noto Sans JP;
      font-size: 1.2em;
      font-weight: bold;
      margin-bottom: 12px;
    }}
    .label {{
      font-size: 1.0em;
      font-family: Noto Sans JP;
      display: inline-block;
      background: #e6f2fb;
      color: #003366;
      border-radius: 8px;
      padding: 6px 8px;
      font-weight: 500;
      margin-bottom: 12px;
    }}
    .description {{
      font-family: Noto Sans JP;
      font-size: 1.0em;
      margin-bottom: 12px;
    }}
    .footer {{
      font-family: Noto Sans JP;
      font-size: 1.0em;
      border-radius: 2px;
      font-weight: 500;
      letter-spacing: 0.03em;
    }}
  </style>
</head>
<body>
  {contents}
</body>
</html>
'''

def azure_updates(date_time):
    data = fetch_azure_updates(date_time)
    if not data:
        logging.info(f"No updates found at {date_time}")
        return
    content_html = build_JA_content_html(data)
    html_template = HTML_TEMPLATE
    final_html = html_template.format(contents=content_html)
    send_mail(final_html)

def fetch_azure_updates(date_time):
    base_url = "https://www.microsoft.com/releasecommunications/api/v2/azure"
    params = {
        "$top": 100,
        "$filter": f"modified ge {date_time}",
        "$orderby": "modified desc",
        "$count": "true",
        "includeFacets": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }    
    response = requests.get(base_url, params=params, headers=headers, timeout=120)
    response.raise_for_status()
    return response.json()["value"]

def init_openai():
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    if not (api_key and api_endpoint):
        raise ValueError("環境変数 AZURE_OPENAI_API_KEY と AZURE_OPENAI_ENDPOINT を設定してください。")
    else:
        return openai.AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=api_endpoint,
        )

def build_JA_content_html(data):
    content_html = ""
    openai = init_openai()
    for item in data:
        title_ja = translate_to_japanese(openai, SYSTEM_PROMPT_TITLE, item['title'])
        products_str = ', '.join(item['products']) if isinstance(item['products'], list) else str(item['products'])
        description_ja = translate_to_japanese(openai, SYSTEM_PROMPT_DESCRIPTION, item['description'])
        created_second = truncate_to_seconds(item['created'])
        content_html += f'''
        <div class="content">
          <div class="title">
            {title_ja}
          </div>
          <div class="label">
            {products_str}
          </div>
          <div class="description">
            {description_ja}
          </div>
          <div class="footer">
            作成日時: {created_second} &nbsp; | &nbsp; 更新日時: {truncate_to_seconds(item['modified'])}
          </div>
        </div>
        '''
    return content_html

def translate_to_japanese(openai, sysytem_prompt, user_prompt):
    try:
        response = openai.chat.completions.create(
            model=os.getenv("MODEL_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": f"{sysytem_prompt}"},
                {"role": "user", "content": f"{user_prompt}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(翻訳エラー: {e})"
    
def truncate_to_seconds(dt_str):
    try:
      dt = datetime.strptime(dt_str[:19], "%Y-%m-%dT%H:%M:%S")
      dt = dt.replace(tzinfo=timezone.utc)
      dt_second_str = dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    except ValueError:
      return dt_str
    return dt_second_str

def send_mail(html):
    try:
        connection_string = os.getenv("MAIL_CONNECTION_STRING")
        sender_address = os.getenv("SENDER_ADDRESS")
        recipient_address = os.getenv("RECIPIENT_ADDRESS")
        client = EmailClient.from_connection_string(connection_string)
        message = {
            "senderAddress": sender_address,
            "recipients": {
                "to": [{"address": recipient_address}]
            },
            "content": {
                "subject": "Azure 更新情報",
                "html": html
            },
            
        }
        poller = client.begin_send(message)
        result = poller.result()
        logging.info(f"Email result : {result}")
    except Exception as ex:
        logging.error(ex)