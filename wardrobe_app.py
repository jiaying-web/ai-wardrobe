import streamlit as st
import requests
import google.generativeai as genai
from PIL import Image
import json
import random

# ==========================================
# ⚙️ 設定區
# ==========================================

# 設定 Google AI
# 優先從 Streamlit Secrets 讀取，如果在本地沒有設定 secret 也不會報錯
try:
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
except:
    GENAI_API_KEY = "" 

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

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

    # 為了讓 session_state 能正確儲存物件，建議轉換成字典
    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "material": self.material
        }

def get_real_weather():
    """使用 Open-Meteo 免費 API 獲取台北天氣"""
    try:
        # 台北的經緯度 (25.03, 121.56)
        url = "https://api.open-meteo.com/v1/forecast?latitude=25.03&longitude=121.56&current_weather=true"
        response = requests.get(url)
        data = response.json()
        temp = data['current_weather']['temperature']
        return temp
    except:
        return 25.0 # 如果抓取失敗，預設 25 度

def analyze_image_with_ai(image):
    """使用 Google Gemini 辨識衣服"""
    if not GENAI_API_KEY:
        st.error("尚未設定 API Key")
        return None
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = """
    你是一個服裝辨識專家。請分析這張圖片中的主要衣物。
    請只回傳一個 JSON 格式，包含以下欄位：
    {"name": "簡短名稱(例如: 藍色牛仔外套)", "category": "上衣/下身/外套/飾品", "color": "顏色", "material": "推測材質"}
    不要回傳任何 Markdown 格式 (如 ```json ... ```)，只要純 JSON 文字。
    """
    try:
        response = model.generate_content([prompt, image])
        # 清理回應文字，確保是 JSON
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI 辨識失敗: {e}")
        return None

# ==========================================
# 📱 網頁介面 (UI)
# ==========================================

st.set_page_config(page_title="AI 智能衣櫃 Pro", page_icon="👗")

# --- 1. 登入系統 (簡易版) ---
if 'user_name' not in st.session_state:
    st.title("🔐 歡迎來到 AI 衣櫃")
    st.markdown("請輸入名字以建立你的專屬衣櫃")
    name_input = st.text_input("你的名字：")
    if st.button("進入衣櫃"):
        if name_input:
            st.session_state.user_name = name_input
            # 初始化衣櫃資料
            if 'wardrobe' not in st.session_state:
                st.session_state.wardrobe = []
                # 預設給幾件衣服當範例
                st.session_state.wardrobe.append(ClothingItem("白色素T", "上衣", "白", "棉"))
                st.session_state.wardrobe.append(ClothingItem("牛仔褲", "下身", "藍", "牛仔布"))
            st.rerun()
    st.stop() 

# --- 2. 登入後的主畫面 ---
with st.sidebar:
    st.write(f"👤 使用者：**{st.session_state.user_name}**")
    if st.button("登出"):
        del st.session_state.user_name
        st.rerun()
    st.divider()
    st.info("💡 小提示：去「AI 入庫」上傳照片試試看！")

st.title(f"👗 {st.session_state.user_name} 的智能衣櫃")

# 分頁設計
tab1, tab2, tab3 = st.tabs(["🌤️ 智能穿搭", "📸 AI 入庫", "🗄️ 衣櫃管理"])

# --- 分頁 1: 智能穿搭 (接真實天氣) ---
with tab1:
    st.subheader("今日台北天氣")
    
    # 自動抓天氣
    if 'current_temp' not in st.session_state:
        st.session_state.current_temp = get_real_weather()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("即時氣溫", f"{st.session_state.current_temp}°C")
    with col2:
        temp = st.session_state.current_temp
        if temp >= 28:
            st.info("🥵 天氣炎熱，建議穿著透氣涼爽的衣物！(短袖、棉麻)")
        elif temp < 20:
            st.info("🥶 天氣偏冷，記得帶件外套喔！(洋蔥式穿法)")
        else:
            st.success("😊 天氣舒適，怎麼穿都好看！")

    st.divider()

    if st.button("✨ 生成今日穿搭建議", use_container_width=True, type="primary"):
        wardrobe = st.session_state.wardrobe
        if not wardrobe:
            st.warning("衣櫃是空的，快去「AI 入庫」新增衣服吧！")
        else:
            tops = [x for x in wardrobe if x.category == "上衣"]
            bottoms = [x for x in wardrobe if x.category == "下身"]
            
            if tops and bottoms:
                # 簡單隨機搭配
                top = random.choice(tops)
                bottom = random.choice(bottoms)
                
                st.balloons()
                st.subheader("💡 今天的推薦搭配：")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### 👕 上身\n**{top.name}**\n\n<span style='color:gray'>{top.material} / {top.color}</span>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"### 👖 下身\n**{bottom.name}**\n\n<span style='color:gray'>{bottom.material} / {bottom.color}</span>", unsafe_allow_html=True)
            else:
                st.error("無法組成完整搭配（缺少上衣或褲子），請先去新增衣物！")

# --- 分頁 2: AI 入庫 (拍照辨識) ---
with tab2:
    st.header("📸 新增衣物")
    st.write("上傳衣服照片，AI 會自動幫你填寫資料！")
    
    if not GENAI_API_KEY:
        st.error("⚠️ 偵測不到 Google API Key，請先設定 Secrets！")
        
    uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"])
    
    # 用 session_state 暫存 AI 辨識結果，避免重新整理後消失
    if 'ai_result' not in st.session_state:
        st.session_state.ai_result = {}

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="預覽圖片", width=200)
        
        if GENAI_API_KEY and st.button("🤖 呼叫 AI 辨識", type="primary"):
            with st.spinner("AI 正在分析這件衣服..."):
                result = analyze_image_with_ai(image)
                if result:
                    st.session_state.ai_result = result
                    st.success("辨識成功！")
                else:
                    st.error("辨識失敗，請稍後再試")

    # 取得預設值 (如果有 AI 結果就用 AI 的，否則留空)
    res = st.session_state.ai_result
    
    st.markdown("### 確認資訊")
    with st.form("add_item_form"):
        name = st.text_input("名稱", value=res.get("name", ""))
        category = st.selectbox("類別", ["上衣", "下身", "外套", "飾品"], 
                              index=["上衣", "下身", "外套", "飾品"].index(res.get("category", "上衣")) if res.get("category") in ["上衣", "下身", "外套", "飾品"] else 0)
        color = st.text_input("顏色", value=res.get("color", ""))
        material = st.text_input("材質", value=res.get("material", ""))
        
        submitted = st.form_submit_button("確認加入衣櫃", use_container_width=True)
        
        if submitted:
            if name:
                new_item = ClothingItem(name, category, color, material)
                st.session_state.wardrobe.append(new_item)
                # 清空暫存
                st.session_state.ai_result = {}
                st.success(f"✅ 已成功加入：{name}")
                st.rerun()
            else:
                st.warning("請輸入衣物名稱")

# --- 分頁 3: 衣櫃管理 ---
with tab3:
    st.subheader("我的衣櫃庫存")
    if not st.session_state.wardrobe:
        st.info("目前衣櫃是空的")
    else:
        for i, item in enumerate(st.session_state.wardrobe):
            with st.expander(f"{i+1}. {item.name} ({item.category})"):
                st.write(f"**顏色：** {item.color}")
                st.write(f"**材質：** {item.material}")
                if st.button("刪除這件", key=f"del_{i}"):
                    st.session_state.wardrobe.pop(i)
                    st.rerun()