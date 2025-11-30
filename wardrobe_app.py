import streamlit as st
import requests
import google.generativeai as genai
from PIL import Image
import json
import random
import os

# ==========================================
# ⚙️ 設定區
# ==========================================

# 設定 Google AI
try:
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
except:
    GENAI_API_KEY = "" 

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

# 定義資料庫檔案名稱
DB_FILE = "wardrobe_db.json"

# ==========================================
# 🧠 核心邏輯
# ==========================================

class ClothingItem:
    def __init__(self, name, category, color, material):
        self.name = name
        self.category = category
        self.color = color
        self.material = material

    def __repr__(self):
        return f"{self.name}"

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "material": self.material
        }

    @staticmethod
    def from_dict(data):
        return ClothingItem(data["name"], data["category"], data["color"], data["material"])

# --- 資料庫存取函式 ---
def load_all_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_all_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_current_user_data():
    if 'user_name' in st.session_state and 'wardrobe' in st.session_state:
        db = load_all_data()
        user_items = [item.to_dict() for item in st.session_state.wardrobe]
        db[st.session_state.user_name] = user_items
        save_all_data(db)

# --- 其他功能 ---
def get_real_weather():
    """使用 Open-Meteo 免費 API 獲取新竹市天氣"""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=24.81&longitude=120.97&current_weather=true"
        response = requests.get(url)
        data = response.json()
        temp = data['current_weather']['temperature']
        return temp
    except:
        return 25.0 

def analyze_image_with_ai(image):
    """使用 Google Gemini 辨識衣服"""
    if not GENAI_API_KEY:
        st.error("⚠️ 尚未設定 API Key，無法使用 AI 辨識。")
        return None
    
    # 使用更穩定快速的模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 簡化 Prompt，提高成功率
    prompt = """
    分析這張圖片中的衣物。
    請回傳純 JSON 格式，不要有任何 Markdown (如 ```json) 或其他文字。
    格式如下：
    {
        "name": "衣物簡短名稱 (例如: 藍色牛仔外套)",
        "category": "請從 [上衣, 下身, 外套, 飾品] 中選一個最接近的",
        "color": "顏色",
        "material": "材質"
    }
    """
    try:
        response = model.generate_content([prompt, image])
        
        # 嘗試清理並解析 JSON
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        
        return json.loads(clean_text)

    except Exception as e:
        # 在終端機印出詳細錯誤，方便除錯
        print(f"AI Error: {e}")
        st.error(f"AI 辨識失敗，請手動輸入資料。")
        return None

# ==========================================
# 📱 網頁介面 (UI)
# ==========================================

st.set_page_config(page_title="AI 智能衣櫃 Pro", page_icon="👗")

# --- 1. 登入系統 ---
if 'user_name' not in st.session_state:
    st.title("🔐 歡迎來到 AI 衣櫃")
    st.markdown("請輸入名字以建立你的專屬衣櫃（系統會記住你的衣服喔！）")
    name_input = st.text_input("你的名字：")
    
    if st.button("進入衣櫃"):
        if name_input:
            st.session_state.user_name = name_input
            db = load_all_data()
            if name_input in db:
                st.session_state.wardrobe = [ClothingItem.from_dict(item) for item in db[name_input]]
                st.toast(f"歡迎回來，{name_input}！", icon="👋")
            else:
                st.session_state.wardrobe = []
                st.session_state.wardrobe.append(ClothingItem("白色素T", "上衣", "白", "棉"))
                st.session_state.wardrobe.append(ClothingItem("牛仔褲", "下身", "藍", "牛仔布"))
                st.session_state.wardrobe.append(ClothingItem("防風外套", "外套", "黑", "尼龍"))
                save_current_user_data()
                st.toast(f"嗨 {name_input}，已建立新衣櫃！", icon="🎁")
            st.rerun()
    st.stop() 

# --- 2. 主畫面 ---
with st.sidebar:
    st.write(f"👤 使用者：**{st.session_state.user_name}**")
    if st.button("登出"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.divider()
    st.info("💡 現在你的衣櫃有記憶功能囉！重新整理網頁也不會消失。")

st.title(f"👗 {st.session_state.user_name} 的智能衣櫃")

tab1, tab2, tab3 = st.tabs(["🌤️ 智能穿搭", "📸 AI 入庫", "🗄️ 衣櫃管理"])

# --- 分頁 1: 智能穿搭 ---
with tab1:
    st.subheader("今日新竹天氣")
    
    if 'current_temp' not in st.session_state:
        st.session_state.current_temp = get_real_weather()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("即時氣溫", f"{st.session_state.current_temp}°C")
    with col2:
        temp = st.session_state.current_temp
        if temp >= 28:
            st.info("🥵 天氣炎熱，建議穿短袖！")
        elif temp < 20:
            st.info("🥶 天氣偏冷，幫你搭配一件外套！")
        else:
            st.success("😊 天氣舒適，怎麼穿都好看！")

    st.divider()

    wardrobe = st.session_state.wardrobe
    tops = [x for x in wardrobe if x.category == "上衣"]
    bottoms = [x for x in wardrobe if x.category == "下身"]
    outers = [x for x in wardrobe if x.category == "外套"]

    st.caption(f"📊 目前可選庫存：上衣 {len(tops)} 件 / 下身 {len(bottoms)} 件 / 外套 {len(outers)} 件")

    if st.button("✨ 生成今日穿搭建議", use_container_width=True, type="primary"):
        if not tops or not bottoms:
            st.warning("⚠️ 無法搭配！請檢查「AI 入庫」是否有足夠的上衣和褲子。")
        else:
            top = random.choice(tops)
            bottom = random.choice(bottoms)
            
            selected_outer = None
            if st.session_state.current_temp < 20 and outers:
                selected_outer = random.choice(outers)
            
            st.balloons()
            st.subheader("💡 今天的推薦搭配：")
            
            if selected_outer:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"### 👕 上身\n**{top.name}**\n\n<small>{top.color}</small>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"### 👖 下身\n**{bottom.name}**\n\n<small>{bottom.color}</small>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"### 🧥 外套\n**{selected_outer.name}**\n\n<small>{selected_outer.color}</small>", unsafe_allow_html=True)
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### 👕 上身\n**{top.name}**\n\n<small>{top.color}</small>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"### 👖 下身\n**{bottom.name}**\n\n<small>{bottom.color}</small>", unsafe_allow_html=True)

# --- 分頁 2: AI 入庫 ---
with tab2:
    st.header("📸 新增衣物")
    
    if not GENAI_API_KEY:
        st.error("⚠️ 請設定 Secrets 才能使用 AI 功能")
        
    uploaded_file = st.file_uploader("上傳照片", type=["jpg", "png", "jpeg"])
    
    if 'ai_result' not in st.session_state:
        st.session_state.ai_result = {}

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="預覽圖片", width=200)
        
        if GENAI_API_KEY and st.button("🤖 呼叫 AI 辨識", type="primary"):
            with st.spinner("AI 正在分析..."):
                result = analyze_image_with_ai(image)
                if result:
                    st.session_state.ai_result = result
                    st.success("辨識成功！請確認下方資訊並按「加入」。")

    res = st.session_state.ai_result
    
    with st.form("add_item_form"):
        name = st.text_input("名稱", value=res.get("name", ""))
        
        cat_options = ["上衣", "下身", "外套", "飾品"]
        ai_cat = res.get("category", "上衣")
        cat_index = cat_options.index(ai_cat) if ai_cat in cat_options else 0
        
        category = st.selectbox("類別", cat_options, index=cat_index)
        color = st.text_input("顏色", value=res.get("color", ""))
        material = st.text_input("材質", value=res.get("material", ""))
        
        if st.form_submit_button("確認加入衣櫃", use_container_width=True):
            if name:
                new_item = ClothingItem(name, category, color, material)
                st.session_state.wardrobe.append(new_item)
                save_current_user_data()
                
                st.session_state.ai_result = {} 
                
                # ✅ 這裡加上更明顯的成功提示
                st.success(f"✅ 成功加入！{name} 已存入衣櫃。")
                st.balloons() # 放氣球慶祝
                
                # 稍微等待一下再重新整理，讓使用者看到提示
                import time
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("請輸入名稱")

# --- 分頁 3: 衣櫃管理 ---
with tab3:
    st.subheader("我的衣櫃庫存")
    if not st.session_state.wardrobe:
        st.info("衣櫃是空的")
    else:
        for i, item in enumerate(st.session_state.wardrobe):
            with st.expander(f"{i+1}. {item.name} ({item.category})"):
                st.write(f"顏色：{item.color} | 材質：{item.material}")
                if st.button("刪除", key=f"del_{i}"):
                    st.session_state.wardrobe.pop(i)
                    save_current_user_data()
                    st.rerun()