import streamlit as st
import requests
from PIL import Image
import json
import random
import os
import uuid  # 用來產生唯一的圖片檔名

# ==========================================
# ⚙️ 設定區
# ==========================================

# 定義資料庫檔案名稱
DB_FILE = "wardrobe_db.json"
# 定義圖片存放資料夾
IMG_DIR = "images"

# 確保圖片資料夾存在
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

# ==========================================
# 🧠 核心邏輯
# ==========================================

class ClothingItem:
    def __init__(self, name, category, color, material, image_path=None):
        self.name = name
        self.category = category
        self.color = color
        self.material = material
        self.image_path = image_path # 新增圖片路徑屬性

    def __repr__(self):
        return f"{self.name}"

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "material": self.material,
            "image_path": self.image_path
        }

    @staticmethod
    def from_dict(data):
        # 使用 .get() 以防舊資料沒有 image_path 欄位時報錯
        return ClothingItem(
            data["name"], 
            data["category"], 
            data["color"], 
            data["material"],
            data.get("image_path") # 讀取圖片路徑
        )

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

def save_uploaded_image(uploaded_file):
    """將上傳的圖片存到 images 資料夾"""
    if uploaded_file is None:
        return None
    
    # 產生一個唯一的檔名 (避免檔名重複)
    file_ext = uploaded_file.name.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(IMG_DIR, unique_filename)
    
    # 存檔
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

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

def find_similar_items(query, wardrobe):
    """搜尋衣櫃中類似的物品"""
    query = query.lower()
    similar_items = []
    keywords = query.split()
    
    for item in wardrobe:
        score = 0
        item_text = f"{item.name} {item.color} {item.material} {item.category}".lower()
        for word in keywords:
            if word in item_text:
                score += 1
        if score > 0:
            similar_items.append(item)
    return similar_items

# ==========================================
# 📱 網頁介面 (UI)
# ==========================================

st.set_page_config(page_title="AI 智能衣櫃", page_icon="👗")

# --- 1. 登入系統 ---
if 'user_name' not in st.session_state:
    st.title("🔐 歡迎來到 AI 衣櫃")
    st.markdown("請輸入名字以建立你的專屬衣櫃")
    name_input = st.text_input("你的名字：")
    
    if st.button("進入衣櫃"):
        if name_input:
            st.session_state.user_name = name_input
            db = load_all_data()
            if name_input in db:
                st.session_state.wardrobe = [ClothingItem.from_dict(item) for item in db[name_input]]
                st.toast(f"歡迎回來，{name_input}！", icon="👋")
            else:
                # 新用戶預設資料
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
    st.info("💡 這次更新後，在「購物建議」可以直接瀏覽分類，不用打字也能檢查衣櫃喔！")

st.title(f"👗 {st.session_state.user_name} 的智能衣櫃")

tab1, tab2, tab3, tab4 = st.tabs(["🌤️ 智能穿搭", "🛍️ 購物建議", "➕ 新增衣物", "🗄️ 衣櫃管理"])

# --- 分頁 1: 智能穿搭 (顯示圖片版) ---
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
            st.warning("⚠️ 無法搭配！請檢查「新增衣物」是否有足夠的上衣和褲子。")
        else:
            top = random.choice(tops)
            bottom = random.choice(bottoms)
            
            selected_outer = None
            if st.session_state.current_temp < 20 and outers:
                selected_outer = random.choice(outers)
            
            st.balloons()
            st.subheader("💡 今天的推薦搭配：")
            
            # 定義顯示衣服的函式 (包含圖片)
            def show_outfit_card(title, item):
                st.markdown(f"### {title}")
                # 如果有圖片路徑且檔案存在，就顯示圖片
                if item.image_path and os.path.exists(item.image_path):
                    st.image(item.image_path, use_container_width=True)
                else:
                    # 沒有圖片時顯示預設圖示
                    if "上衣" in title: icon = "👕"
                    elif "下身" in title: icon = "👖"
                    else: icon = "🧥"
                    st.markdown(f"<div style='font-size: 50px; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
                
                st.markdown(f"**{item.name}**")
                st.caption(f"{item.color} / {item.material}")

            if selected_outer:
                c1, c2, c3 = st.columns(3)
                with c1: show_outfit_card("👕 上身", top)
                with c2: show_outfit_card("👖 下身", bottom)
                with c3: show_outfit_card("🧥 外套", selected_outer)
            else:
                c1, c2 = st.columns(2)
                with c1: show_outfit_card("👕 上身", top)
                with c2: show_outfit_card("👖 下身", bottom)

# --- 分頁 2: 購物建議 (優化版) ---
with tab2:
    st.header("🛍️ 購物小幫手")
    
    # 1. 庫存統計儀表板
    wardrobe = st.session_state.wardrobe
    counts = {
        "上衣": len([x for x in wardrobe if x.category == "上衣"]),
        "下身": len([x for x in wardrobe if x.category == "下身"]),
        "外套": len([x for x in wardrobe if x.category == "外套"]),
        "飾品": len([x for x in wardrobe if x.category == "飾品"]),
    }
    
    st.caption("📊 你的衣櫃庫存概況：")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("上衣", f"{counts['上衣']} 件")
    c2.metric("下身", f"{counts['下身']} 件")
    c3.metric("外套", f"{counts['外套']} 件")
    c4.metric("飾品", f"{counts['飾品']} 件")
    st.divider()

    st.subheader("🔍 檢查是否有類似款")
    
    # 2. 搜尋與篩選區
    col_search, col_filter = st.columns([2, 1])
    
    with col_search:
        search_query = st.text_input("輸入關鍵字搜尋", placeholder="例如: 白色T恤...")
    with col_filter:
        filter_category = st.selectbox("或按類別瀏覽", ["(全部顯示)", "上衣", "下身", "外套", "飾品"])

    # 3. 顯示邏輯
    display_items = []
    
    # 如果有輸入關鍵字，優先使用關鍵字搜尋
    if search_query:
        display_items = find_similar_items(search_query, wardrobe)
        if not display_items:
            st.info("找不到相關物品，衣櫃裡沒有類似款！")
    # 如果沒有關鍵字，但選了特定類別，顯示該類別所有物品
    elif filter_category != "(全部顯示)":
        display_items = [x for x in wardrobe if x.category == filter_category]
        if not display_items:
            st.info(f"你的衣櫃裡還沒有 {filter_category} 喔！")
    # 如果什麼都沒選，預設顯示全部 (或提示使用者)
    else:
        st.info("👆 請輸入關鍵字，或選擇類別來查看衣櫃內容。")
        display_items = [] # 預設不顯示，避免畫面太亂，或者也可以設為 wardrobe 顯示全部

    # 4. 顯示結果卡片
    if display_items:
        st.write(f"找到 {len(display_items)} 件物品：")
        cols = st.columns(3)
        for idx, item in enumerate(display_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    # 顯示圖片
                    if item.image_path and os.path.exists(item.image_path):
                        st.image(item.image_path, use_container_width=True)
                    else:
                        st.markdown("<div style='height:100px; background-color:#f0f2f6; display:flex; align-items:center; justify-content:center;'>無圖片</div>", unsafe_allow_html=True)
                    
                    st.write(f"**{item.name}**")
                    st.caption(f"{item.category} / {item.color} / {item.material}")

# --- 分頁 3: 新增衣物 (包含存檔圖片) ---
with tab3:
    st.header("📸 新增衣物")
    
    uploaded_file = st.file_uploader("上傳照片 (推薦)", type=["jpg", "png", "jpeg"])
    
    # 預覽圖片
    if uploaded_file:
        st.image(uploaded_file, caption="預覽中...", width=200)

    with st.form("add_item_form"):
        name = st.text_input("名稱 (例如: 黑色帽T)")
        category = st.selectbox("類別", ["上衣", "下身", "外套", "飾品"])
        color = st.text_input("顏色")
        material = st.text_input("材質")
        
        if st.form_submit_button("確認加入衣櫃", use_container_width=True):
            if name:
                # 1. 先儲存圖片
                saved_image_path = save_uploaded_image(uploaded_file)
                
                # 2. 建立新物件 (包含圖片路徑)
                new_item = ClothingItem(name, category, color, material, saved_image_path)
                st.session_state.wardrobe.append(new_item)
                
                # 3. 存入資料庫
                save_current_user_data()
                
                st.success(f"✅ 成功加入！{name}")
                st.balloons()
                
                import time
                time.sleep(1.0)
                st.rerun()
            else:
                st.warning("請輸入名稱")

# --- 分頁 4: 衣櫃管理 (新增編輯功能 + 圖片更換) ---
with tab4:
    st.subheader("我的衣櫃庫存")
    if not st.session_state.wardrobe:
        st.info("衣櫃是空的")
    else:
        # 遍歷所有衣服
        for i, item in enumerate(st.session_state.wardrobe):
            with st.expander(f"{i+1}. {item.name} ({item.category})"):
                
                # 檢查是否處於「編輯模式」
                edit_key = f"edit_mode_{i}"
                if st.session_state.get(edit_key, False):
                    # === 編輯模式 ===
                    with st.form(f"edit_form_{i}"):
                        st.caption("✏️ 編輯中...")
                        
                        # 允許更換圖片
                        new_image_file = st.file_uploader("更換照片 (選填)", type=["jpg", "png", "jpeg"], key=f"edit_img_{i}")
                        
                        new_name = st.text_input("名稱", value=item.name)
                        new_cat = st.selectbox("類別", ["上衣", "下身", "外套", "飾品"], index=["上衣", "下身", "外套", "飾品"].index(item.category))
                        new_color = st.text_input("顏色", value=item.color)
                        new_mat = st.text_input("材質", value=item.material)
                        
                        col_save, col_cancel = st.columns(2)
                        if col_save.form_submit_button("💾 儲存修改", type="primary"):
                            # 如果有上傳新圖片，就更新路徑，否則維持原樣
                            if new_image_file:
                                item.image_path = save_uploaded_image(new_image_file)
                            
                            # 更新其他文字資料
                            item.name = new_name
                            item.category = new_cat
                            item.color = new_color
                            item.material = new_mat
                            
                            # 存檔
                            save_current_user_data()
                            # 關閉編輯模式
                            st.session_state[edit_key] = False
                            st.rerun()
                        
                        if col_cancel.form_submit_button("取消"):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    # === 檢視模式 ===
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        # 顯示圖片
                        if item.image_path and os.path.exists(item.image_path):
                            st.image(item.image_path, use_container_width=True)
                        else:
                            st.text("無圖片")
                    
                    with c2:
                        st.write(f"**顏色：** {item.color}")
                        st.write(f"**材質：** {item.material}")
                    
                    # 按鈕區
                    b1, b2 = st.columns(2)
                    if b1.button("✏️ 編輯", key=f"btn_edit_{i}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    
                    if b2.button("🗑️ 刪除", key=f"btn_del_{i}"):
                        st.session_state.wardrobe.pop(i)
                        save_current_user_data()
                        st.rerun()