import subprocess
import sys

# 將requirements.txt的內容內建到程式中

requirements_content = """
Flask
requests
pyngrok == 7.2.2
google-generativeai
line-bot-sdk
"""

# 儲存requirements.txt的內容到檔案
def create_requirements_file():
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    print("已創建 requirements.txt")

# 安裝requirements.txt的依賴
def install_requirements():
    try:
        print("開始安裝requirements.txt中的依賴...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True, capture_output=True, text=True)
        print(result.stdout)  # 輸出安裝過程中的標準輸出
    except subprocess.CalledProcessError as e:
        print(f"安裝失敗，錯誤代碼: {e.returncode}")
        print(f"錯誤輸出: {e.stderr}")  # 顯示錯誤訊息
        sys.exit(1)

# 在Flask應用啟動前安裝依賴
create_requirements_file()  # 創建 requirements.txt
install_requirements()  # 安裝依賴

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import requests
import os
from pyngrok import ngrok, conf, installer
import subprocess
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
# 第一次使用時下載模型（只需做一次）
import os
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger, CkipNerChunker
# Initialize drivers
ws_driver  = CkipWordSegmenter(model="bert-base")
pos_driver = CkipPosTagger(model="bert-base")
ner_driver = CkipNerChunker(model="bert-base")
from bs4 import BeautifulSoup
import google.generativeai as genai

def connect_ngrok_safely(addr=5000, domain=None):
    import subprocess as sp

    original_popen = sp.Popen
    def patched_popen(*args, **kwargs):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
        return original_popen(*args, **kwargs)

    sp.Popen = patched_popen

    try:
        if domain:
            return ngrok.connect(addr=addr, domain=domain)
        else:
            return ngrok.connect(addr=addr)
    finally:
        sp.Popen = original_popen


import json

#=====這裡是呼叫的檔案內容=====
from message import *
from new import *
from Function import *
#=====這裡是呼叫的檔案內容=====

#=====python的函數庫==========
import tempfile, os
import re
import datetime
import time
import ssl
#=====python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Channel Access Token
line_bot_api = LineBotApi('QZDvAGYlPSK9AFXyKxrq4DncSBrgVnog8Mx8WBP8B7rp+kL4bbUTrygY8bnSnBeGxtcW8fIvS8umitasGyNWjnmC4HGxvbkd5Bmu9HpKgAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('18ebcff5183621c302f')

# Gemini API 認證金鑰
GEMINI_API_KEY = "AIzaSyCeoQrelT9Z8ETpSMlU"  # 確保已經有API金鑰

# 設定ngrok隧道
pyngrok_config = conf.get_default()

# Check if ngrok is installed, if not, install it
if not os.path.exists(pyngrok_config.ngrok_path):
    myssl = ssl.create_default_context()
    myssl.check_hostname = False
    myssl.verify_mode = ssl.CERT_NONE
    installer.install_ngrok(pyngrok_config.ngrok_path, context=myssl)

# Set ngrok auth token
ngrok.set_auth_token("2wUA3QGBa2tCjFCMLUWvfQU4qpt_3mGSLjSACV8cHN2K7ALDz")

# Start ngrok tunnel

#public_url = ngrok.connect(5000).public_url
#print(f" * Ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:5000\"")

public_url = connect_ngrok_safely(addr=5000, domain="vigorously-pretty-jawfish.ngrok-free.app")

print("固定的 ngrok 網址是：", public_url)

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    # ✅ 賽程或觀賽規則
    if any(kw in msg for kw in ['賽程', '幾點', '今天有沒有', '比賽']):
        message = TextSendMessage(text='你可以到中華職棒的官網查詢賽程的相關資訊：\nhttps://www.cpbl.com.tw/schedule')

    elif any(kw in msg for kw in ['規則', '術語', '觀賽']):
        message = TextSendMessage(text='你可以到野球革命的新手專區找答案：\nhttps://stats.rebas.tw/newbie-zone')

    # ✅ 查詢表格（打者基礎/進階/新數據）
    elif any(kw in msg for kw in ['進階數據', '新數據', '基礎數據']):
        reply = handle_table_query(msg)
        message = TextSendMessage(text=reply)

    # ✅ 查詢個人成績（球員表現）
    elif any(kw in msg for kw in ['成績', '表現', '狀況']):
        reply = handle_stat_query(msg)
        message = TextSendMessage(text=reply)

    # ✅ 查詢排行榜（最多XXX / 最強XXX / XXX王）→ 含進階數據也支援
    elif any(kw in msg for kw in ['最多', '王', '最高', '最強', '最好','最低']):
        pitcher_keywords = ['投手','era', 'era+','whip',
                            '被打擊率','殘壘率','獨立防禦率','fip',
                            '被長打率','安打/九局','h9','全壘打/九局','hr9']
        if any(kkw.lower() in msg.lower() for kkw in pitcher_keywords):
            reply = handle_pitcher_leaderboard_query(msg)
        else:
            reply = handle_leaderboard_query(msg)
        message = TextSendMessage(text=reply)
    # ✅ 其他：送給 Gemini 自然語言理解
    else:
        response = query_gemini_api(msg)
        message = TextSendMessage(text=response)

    line_bot_api.reply_message(event.reply_token, message)


@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

def query_gemini_api(user_query):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(user_query)
    return response.text

#抓取球員名稱
import regex as re  # 注意！用 regex 模組取代 re

def preprocess_text_before_ws(text):
    """
    將人名後接的年份或時間詞切開，避免被 CKIP 錯誤合併。
    """
    # ex: 王威晨2023年 → 王威晨 2023 年
    text = re.sub(r"(\p{Han}+)(20\d{2})年", r"\1 \2 年", text)
    text = re.sub(r"(\p{Han}+)(20\d{2})", r"\1 \2", text)
    text = re.sub(r"(\p{Han}+)(今年|去年|明年)", r"\1 \2", text)
    return text


import unicodedata
import pickle
# 載入球員名單
def normalize_text(s):
    s = unicodedata.normalize("NFKC", s)  # 全形轉半形
    return re.sub(r"[\s\u3000\u200b\ufeff]", "", s) 
# 讀取球員名單
with open(r"C:\Users\林哲宇\Desktop\linebot-master_gemini\player_name_list.pkl", "rb") as f:
    player_name_list = set(normalize_text(name) for name in pickle.load(f))

def extract_player_name(text):
    exclude_pos = {"DET", "P", "C", "T", "VA", "D", "DE", "SHI", "ASP", "FW", "FUNC", "COLON", "COMMACATEGORY"}
    noise_keywords = {"成績", "表現", "成效", "數據", "統計", "打擊", "二軍", "一軍", "熱身賽", "季後", "大賽"}
    year_keywords = {"今年", "去年", "明年"} | {str(y) for y in range(2010, 2035)}

    # ✅ Step 1：優先從整句直接比對球員名單
    for name in sorted(player_name_list, key=len, reverse=True):  # 長的先比
        if name in text:
            print(f"✅ 直接從輸入句中比對到球員：{name}")
            return name

    # ✅ Step 2：若比對失敗，再進行 CKIP 分詞與詞性處理
    text = preprocess_text_before_ws(text)
    words = ws_driver([text])[0]
    pos_tags = pos_driver([words])[0]

    print("🪓 CKIP斷詞結果：", words)
    print("🏷️ CKIP詞性標記：", pos_tags)

    candidates = []

    # 四詞結構：Nb + Nb + · + Nb
    for i in range(len(words) - 3):
        w1, w2, w3, w4 = words[i].strip(), words[i+1].strip(), words[i+2].strip(), words[i+3].strip()
        f1, f2, f3, f4 = pos_tags[i], pos_tags[i+1], pos_tags[i+2], pos_tags[i+3]
        if f1 == f2 == "Nb" and w3 in {"．", "·"} and f4 == "Nb":
            return w1 + w2 + w3 + w4

    # 三詞結構：Nb + · + Nb
    for i in range(len(words) - 2):
        w1, w2, w3 = words[i].strip(), words[i+1].strip(), words[i+2].strip()
        f1, f2, f3 = pos_tags[i], pos_tags[i+1], pos_tags[i+2]
        if f1 == "Nb" and w2 in {"．", "·"} and f3 == "Nb":
            return w1 + w2 + w3

    # 單詞 Nb 候選
    for word, tag in zip(words, pos_tags):
        word = word.strip()
        if tag == "Nb" and word not in noise_keywords and word not in year_keywords:
            candidates.append(word)

    # 雙詞 N 開頭
    for i in range(len(words) - 1):
        w1, w2 = words[i].strip(), words[i+1].strip()
        f1, f2 = pos_tags[i], pos_tags[i+1]
        if f1.startswith("N") and f2.startswith("N"):
            combined = w1 + w2
            if combined not in noise_keywords and 2 <= len(combined) <= 10:
                candidates.append(combined)

    # fallback：若前面都沒有回傳，再從分詞序列中拼接所有 2~4 字，對名單比對
    for i in range(len(words)):
        for j in range(i + 1, min(i + 5, len(words)) + 1):
            phrase = "".join(w.strip() for w in words[i:j])
            if phrase in player_name_list:
                print(f"✅ fallback 比對到：{phrase}")
                return phrase

    print("🧪 玩家候選清單：", candidates)
    return max(candidates, key=len) if candidates else None

# ===== 擷取年份與比賽類型 =====
def extract_year_and_type(text):
    words = ws_driver([text])[0]

    # 將「2024年」→ ["2024", "年"]
    processed_words = []
    for w in words:
        if re.fullmatch(r"\d{4}年", w):
            processed_words.append(w[:4])
            processed_words.append("年")
        else:
            processed_words.append(w)

    print("🔍 處理後斷詞：", processed_words)

    # 提取年份
    year = next((w for w in processed_words if w.isdigit() and len(w) == 4), None)

    # 提取比賽類型（允許出現在整句中的任意位置）
    type_keywords = {
        "台灣大賽": ["台灣大賽", "總冠軍", "總冠軍賽"],
        "季後挑戰賽": ["季後", "挑戰賽"],
        "熱身賽": ["熱身", "官辦"],
        "二軍": ["二軍"],
        "一軍": ["一軍", "例行賽"]
    }

    # 依照優先順序從高階賽事往下匹配
    for key, aliases in type_keywords.items():
        if any(alias in "".join(processed_words) for alias in aliases):
            print(f"✅ 偵測到比賽類型：{key}")
            return year, key

    print("⚠️ 未偵測比賽類型，預設為一軍")
    return year, "一軍"
# ===== 查詢表格數據主控函式 =====

def handle_table_query(user_msg):
    import datetime
    from bs4 import BeautifulSoup
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # 斷詞與抽取資訊
    player_name = extract_player_name(user_msg)
    if not player_name:
        return "❌ 無法辨識球員姓名，請輸入格式如『高宇杰 2024 進階數據』"

    year, _ = extract_year_and_type(user_msg)
    if not year:
        year = str(datetime.datetime.now().year)

    # ✅ 預設為「一軍例行賽」，若有提到「季後」關鍵字才找季後賽
    game_stage = "季後賽" if "季後" in user_msg else "例行賽"

    # 提取要抓的表格種類
    table_keywords = []
    for key in ["基礎數據", "進階數據", "新數據"]:
        if key in user_msg:
            table_keywords.append(key)
    if not table_keywords:
        table_keywords = ["基礎數據"]  # 預設查詢基礎數據

    # 啟動瀏覽器並進入球員頁面
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.rebas.tw")

    # 搜尋球員
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-player-input"))
    )
    search_box.send_keys(player_name)
    search_box.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.searching-result div.player span.name a"))
    )

    results = driver.find_elements(By.CSS_SELECTOR, "div.searching-result div.player span.name a")
    target_url = None
    for r in results:
        if r.text.strip().split(" #")[0] == player_name:
            target_url = r.get_attribute("href")
            break

    if not target_url:
        driver.quit()
        return f"❌ 找不到名為「{player_name}」的球員資料。"

    driver.get(target_url)
    time.sleep(3)

    # 解析頁面
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    all_tables = soup.find_all("table")
    found_tables = []

    for table in all_tables:
        parent_div = table.find_parent("div", class_="sc-oTmZL")
        if not parent_div:
            continue
        h3_title = parent_div.find_previous("h3", class_="stats-title")
        if not h3_title:
            continue
        title_text = h3_title.text.strip()
        if not any(k in title_text for k in table_keywords):
            continue

        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        headers = [th.text.strip() for th in rows[0].find_all("th")]
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) != len(headers):
                continue

            row_data = [td.text.strip() for td in cells]
            row_year = row_data[0]
            row_level = row_data[1]
            row_stage = row_data[2]

            if row_year != year or row_level != "一軍":
                continue
            if game_stage not in row_stage:
                continue

            found_tables.append((title_text, row_year, row_stage, headers, row_data))

    if not found_tables:
        return f"⚠️ 找不到 {player_name} 在 {year} 年 {game_stage} 的指定數據。"
       # 🧠 Gemini prompt 組合
    segments = []
    for title, y, stage, headers, values in found_tables:
        segments.append(f"📊 {title}（{y} 年 {stage}）")
        for h, v in zip(headers, values):
            segments.append(f"{h}: {v}")
        segments.append("")

    prompt = f"""
請幫我說明下列棒球球員的比賽數據內容，請逐項解釋所有數據，並避免籠統說明如「表現不錯」這種敘述，不過年度、層級、球隊這種不用說明。
請注意「打擊率」「OPS」等需依實際內容解釋其意義，不可誤導。
回答中必須寫上表格的名稱，讓使用者知道這些數據是屬於哪個表格。
如有多張表格請以【表格名稱】作為小標題。
呈現時應求美觀，讓使用者能夠清楚理解每個數據的意義，最好以條列式呈現每筆數據。最後做一個總結，說明這位球員在這個賽季的整體表現。
請不要使用 HTML 標籤或 Markdown 語法（如 `*`, `**`, `#` 等），僅使用簡單符號如 ●、: 或 ⬤，讓內容適合 LINE 訊息閱讀。
若你能使用 emoji，請用 ⚾、📊、🔺 等符號來增強表現指標的可視性。
資料如下：
球員：{player_name}，賽季：{year} {game_stage}
{chr(10).join(segments)}
""".strip()

    return query_gemini_api(prompt)






# ===== 成績查詢主控函式 =====
def handle_stat_query(user_msg):
    player_name = extract_player_name(user_msg)
    if not player_name:
        return "❌ 無法辨識球員姓名，請輸入格式如『高宇杰 2024 一軍』"

    year, game_type = extract_year_and_type(user_msg)
    if not year:
        year = str(datetime.datetime.now().year)

    actual_name, season_label, stats = player_pr(player_name, f"{year} {game_type}")
    if not stats:
        return f"⚠️ 沒有找到 {actual_name} 在 {season_label} 的數據"

    data_lines = "\n".join([f"{s[0]}: {s[1]} (PR {s[2]})" for s in stats])
    prompt = f"""
請根據以下數據撰寫一段完整說明，語氣自然但不能省略任何項目，也不要只說「表現很好」等總結句，
且對 PR 值應作正確的解釋，不是指個人的排名，而是個人整個聯盟中的相對位置，例如:PR40代表該選手在該聯盟為只贏過40%的人，PR99代表贏過99%的人
。
在呈現回應時應求美觀，讓使用者能夠清楚理解每個數據的意義，最好以條列式呈現每筆數據，且對於解釋應該盡量詳細，並在所有數據結束後做一個總結，
說明這位球員在這個賽季的整體表現。
請在開頭加上一行簡短摘要，再以條列式列出每筆數據，條列請以「●」符號開頭。
請不要使用 HTML 標籤或 Markdown 語法（如 `*`, `**`, `#` 等），僅使用簡單符號如 ●、: 或 ⬤，讓內容適合 LINE 訊息閱讀。

若你能使用 emoji，請用 ⚾、📊、🔺 等符號來增強表現指標的可視性。

資料如下：
球員：{actual_name}，賽季：{season_label}
{data_lines}
    """.strip()

    return query_gemini_api(prompt)



# ===== Selenium 爬蟲查詢函式 =====
def player_pr(player_name, user_input):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    import time, datetime

    # 🔹 根據使用者輸入判斷賽季關鍵字
    tokens = user_input.split()
    target_year = next((t for t in tokens if t.isdigit() and len(t) == 4), str(datetime.datetime.now().year))

    if "二軍" in user_input:
        target_keyword = f"中職二軍{target_year}年"
    elif any(k in user_input for k in ["台灣大賽", "總冠軍"]):
        target_keyword = f"中職{target_year}年-台灣大賽"
    elif "挑戰賽" in user_input:
        target_keyword = f"中職{target_year}年-季後挑戰賽"
    elif any(k in user_input for k in ["熱身", "官辦"]):
        target_keyword = f"中職{target_year}年-官辦熱身賽"
    else:
        target_keyword = f"中職{target_year}年"

    # 🔹 啟動瀏覽器
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.rebas.tw")

    # 🔹 搜尋球員
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-player-input"))
    )
    search_box.send_keys(player_name)
    search_box.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.searching-result div.player span.name a"))
    )

    results = driver.find_elements(By.CSS_SELECTOR, "div.searching-result div.player span.name a")
    target_url = None
    for r in results:
        if r.text.strip().split(" #")[0] == player_name:
            target_url = r.get_attribute("href")
            break

    if not target_url:
        driver.quit()
        return player_name, user_input, []

    driver.get(target_url)

    # 🔹 等待並擷取下拉選單
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "select"))
    )

    option_map = {}
    for opt in select_element.find_elements(By.TAG_NAME, "option"):
        label = opt.text.strip()
        value = opt.get_attribute("value")
        if value:
            option_map[label] = value

    matched_value = option_map.get(target_keyword)

    if not matched_value:
        driver.quit()
        return player_name, target_keyword, []

    # 🔹 等待 SVG 初始圖表
    Select(select_element).select_by_value(matched_value)

    # 等待新圖表載入
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg")))
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "svg g g g")))
    time.sleep(5)  # 保險延遲一下


    # 🔹 擷取圖表文字
    g_groups = driver.find_elements(By.CSS_SELECTOR, "svg g g g")
    stats = []
    added_labels = set()

    for g in g_groups:
        try:
            texts = g.find_elements(By.TAG_NAME, "text")
            if len(texts) == 3:
                label, value, pr = [t.text.strip() for t in texts]
                if label and value and pr.isdigit() and label not in added_labels:
                    stats.append((label, value, pr))
                    added_labels.add(label)
        except:
            continue

    driver.quit()
    return player_name, target_keyword, stats

# ===== 處理排行榜查詢 =====
def handle_leaderboard_query(msg: str) -> str:
    import re
    import time
    from datetime import datetime
    import traceback
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from ckip_transformers.nlp import CkipWordSegmenter
    global ws_driver

    # ✅ 欄位對應（標準 + 進階）
    STAT_COLUMN_MAP = {
        # 標準數據
        '出賽': '出賽', '打席': '打席', '打數': '打數', '得分': '得分',
        '安打': '安打', '二安': '二安', '三安': '三安', '全壘打': '全壘打',
        '四壞': '四壞', '故意四壞': '故四', '觸身': '觸身',
        '犧牲觸擊': '犧觸', '高飛犧牲打': '犧飛', '盜壘': '盜壘', '盜刺': '盜刺',
        '打點': '打點', '三振': '三振', '打擊率': '打擊率',

        # 進階數據（中英關鍵字皆可）
        'ops': '攻擊指數', '攻擊指數': '攻擊指數',
        'ops+': '攻擊指數+', '攻擊指數+': '攻擊指數+',
        'obp': '上壘率', '上壘率': '上壘率',
        'slg': '長打率', '長打率': '長打率',
        'iso': '純長打率', '純長打率': '純長打率',
        'ifh%': '場內安打率', '場內安打率': '場內安打率',
        'babip': '球入場率', '球入場率': '球入場率',
        'rc': '製分能力', 'rc/pa': '製分能力', '製分能力': '製分能力',
        'woba': '加權上壘率', '加權上壘率': '加權上壘率',
        'bb%': '保送率', '保送率': '保送率',
        'bb/k': '保送/三振', '保送/三振': '保送/三振', '保送三振比': '保送/三振',
        'k%': '被三振率', '被三振率': '被三振率', '三振率': '被三振率',
        'swstr%': '揮空率', '揮空率': '揮空率',
        'sb%': '盜壘成功率', '盜壘成功率': '盜壘成功率'
    }

    ADVANCED_SECTION_KEYWORDS = [
        'ops', 'ops+', 'obp', 'slg', 'iso', 'babip', 'rc', 'rc/pa', '製分能力',
        'woba', 'bb%', '保送率', '保送三振比', '保送/三振', 'k%', '被三振率', '三振率','揮空率',
        '場內安打率', '球入場率', '加權上壘率', '純長打率', '進階', 'sb%', '盜壘成功率'
    ]

    # ✅ 斷詞與轉小寫比對
    tokens = ws_driver([msg])[0]
    token_str = ''.join(tokens).lower()
    sorted_keywords = sorted(
        [(kw.lower(), col) for kw, col in STAT_COLUMN_MAP.items()],
        key=lambda x: -len(x[0])
    )
    stat_col_name = next((col for kw, col in sorted_keywords if kw in token_str), None)

    if not stat_col_name:
        return "請問你想查哪一項打者數據最多？例如：OPS、BABIP、全壘打等。"

    # ✅ 判斷進階數據頁面
    is_advanced = any(kw in token_str for kw in ADVANCED_SECTION_KEYWORDS)

    # ✅ 抓取年份
    match = re.search(r'(\d{4})', msg)
    year = match.group(1) if match else '2025'
    dropdown_label = f"中職{year}年"

    # ✅ 頁面網址
    url = f"https://www.rebas.tw/season/CPBL-{year}-JO/leaderboard?stats=batter&section="
    url += "advanced" if is_advanced else "standard"

    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1400, 1000)

        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        Select(driver.find_element(By.TAG_NAME, "select")).select_by_visible_text(dropdown_label)
        time.sleep(1.5)

        toggle_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'label.switch'))
        )
        toggle_label.click()
        time.sleep(1)

        headers = driver.find_elements(By.CSS_SELECTOR, "table thead th")
        target_index = None
        for i, th in enumerate(headers):
            if stat_col_name in th.text:
                th.click()
                target_index = i
                break

        if target_index is None:
            driver.quit()
            return f"⚠️ 找不到欄位「{stat_col_name}」，請檢查是否拼寫正確。"

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr")))
        row = driver.find_element(By.CSS_SELECTOR, "tbody tr")
        tds = row.find_elements(By.CSS_SELECTOR, "td")
        player = tds[0].find_element(By.TAG_NAME, "a").text
        value = tds[target_index].text
        driver.quit()
    
        prompt = f'''請用自然語氣說明：在中職{year}年賽季中，{stat_col_name}最高或最好的球員是{player}，數值為 {value}。
        
        對於較負面的數據（如三振率、揮空率等），請改以「最高」來陳述，不要使用「最好」。
        '''
        return query_gemini_api(prompt)

    except Exception as e:
        print(traceback.format_exc())
        try:
            driver.quit()
        except:
            pass
        return f"查詢失敗，請稍後再試：{str(e)}"


def handle_pitcher_leaderboard_query(msg: str) -> str:
    import re
    import time
    import traceback
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from ckip_transformers.nlp import CkipWordSegmenter
    global ws_driver

    # ✅ 投手數據欄位對應（標準 + 進階）
    STAT_COLUMN_MAP = {
        #基礎數據
        '出賽':'出賽', '先發':'先發', '勝':'勝', '勝場':'勝', 
        '局數':"局數", '局':"局", '面對打者':'面對打者', '打者':'面對打者',
        '失分':'失分', '責失':'責失', '被安打':'被安打', '二安':'二安',
        '三安':'三安','全壘打':'全壘打', '四壞':'四壞', '保送':'四壞',
        '三振':'三振', '被盜壘':'被盜壘',
        #進階數據
        '防禦率': '防禦率', 'era': '防禦率',
        'era+': '防禦率+', '防禦率+': '防禦率+',
        'fip': '獨立防禦率', '獨立防禦率': '獨立防禦率',
        'whip': '被上壘率', '被上壘率': '被上壘率',
        'lob%': '殘壘率', '殘壘率': '殘壘率',
        'ifh%': '場內安打率', '場內安打率': '場內安打率',
        '被打擊率': '打擊率', '被長打率': '長打率',
        'h9': '安打/九局', '安打/九局': '安打/九局',
        'hr9': '全壘打/九局', '全壘打/九局': '全壘打/九局',
        'k%': '三振率', '三振率': '三振率',
        'swstr%': '揮空率', '揮空率': '揮空率'
    }

    HIGHER_BETTER = {'防禦率+','三振率', '揮空率', '出賽', '先發', '勝', '勝場', 
        '局數', '局', '面對打者', '打者','失分', '責失', '被安打', '二安',
        '三安','全壘打', '四壞', '保送',
        '三振', '被盜壘'}
    ADVANCED_SECTION_KEYWORDS = [
        'era','防禦率','era+','防禦率+', 'fip','獨立防禦率', 'whip',
        '被上壘率', 'lob%','殘壘率', 'babip','場內安打率', 'avg','被打擊率',
        'obp','上壘率', 'slg','被長打率'
        'h9', '安打/九局','hr9','全壘打/九局', '保送率', 'bb%',  'k%', '被三振率', '三振率','揮空率',
        'Whiff%', 'sb%', '被盜壘率' 
    ]

    # ✅ 斷詞與欄位比對
    tokens = ws_driver([msg])[0]
    token_str = ''.join(tokens).lower()
    sorted_keywords = sorted(
        [(kw.lower(), col) for kw, col in STAT_COLUMN_MAP.items()],
        key=lambda x: -len(x[0])
    )
    stat_col_name = next((col for kw, col in sorted_keywords if kw in token_str), None)
    

    if not stat_col_name:
        return "請問你想查哪一項投手數據最好？例如：ERA、FIP、三振率等。"
    # ✅ 判斷進階數據頁面
    
    is_advanced = any(kw in token_str for kw in ADVANCED_SECTION_KEYWORDS)
    
    # ✅ 抓年份
    match = re.search(r'(\d{4})', msg)
    year = match.group(1) if match else '2025'
    dropdown_label = f"中職{year}年"

    section = "advanced" if is_advanced else "standard"
    url = f"https://www.rebas.tw/season/CPBL-2025-JO/leaderboard?stats=pitcher&section={section}"


    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1400, 1000)

        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        Select(driver.find_element(By.TAG_NAME, "select")).select_by_visible_text(dropdown_label)
        time.sleep(1.5)

        toggle_label = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'label.switch'))
        )

        # 避免廣告遮擋：先捲動 + 用 JavaScript 點擊
        try:
            driver.execute_script("arguments[0].scrollIntoView();", toggle_label)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", toggle_label)
            time.sleep(1)
        except Exception as e:
            print("⚠️ 無法點擊 switch：", e)


        headers = driver.find_elements(By.CSS_SELECTOR, "table thead th")
        target_index = None
        for i, th in enumerate(headers):
            if stat_col_name in th.text:
                # 先點一下排序
                th.click()
                time.sleep(0.5)
                # 若越低越好則點兩次（升冪）
                if stat_col_name not in HIGHER_BETTER:
                    th.click()
                    time.sleep(0.5)
                target_index = i
                break

        if target_index is None:
            driver.quit()
            return f"⚠️ 找不到欄位「{stat_col_name}」，請檢查是否拼寫正確。"

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr")))
        row = driver.find_element(By.CSS_SELECTOR, "tbody tr")
        tds = row.find_elements(By.CSS_SELECTOR, "td")
        player = tds[0].find_element(By.TAG_NAME, "a").text
        value = tds[target_index].text
        driver.quit()

        prompt = f'''請用自然語氣說明：在中職{year}年賽季中，{stat_col_name}最佳的投手是{player}，數值為 {value}。

若是「era+」、「三振率」、「揮空率」，請說成「最高」；其餘數據越低越好，請說成「最低」。'''
        return query_gemini_api(prompt)

    except Exception as e:
        print(traceback.format_exc())
        try:
            driver.quit()
        except:
            pass
        return f"查詢失敗，請稍後再試：{str(e)}"

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
