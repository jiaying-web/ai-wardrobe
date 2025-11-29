import streamlit as st
import random
from datetime import datetime


class ClothingItem:
    def __init__(self, name, category, color, material, style_tags):
        self.name = name
        self.category = category
        self.color = color
        self.material = material
        self.style_tags = style_tags

    def __repr__(self):
        return f"{self.name} ({self.material})"

# 初始化 Session State (讓網頁重新整理時不會忘記你的衣服)
if 'wardrobe' not in st.session_state:
    st.session_state.wardrobe = []
    # 預設放入一些範例資料
    default_items = [
        ("白色素面T恤", "上衣", "白", "棉", ["休閒"]),
        ("亞麻襯衫", "上衣", "米色", "麻", ["文青"]),
        ("牛仔寬褲", "下身", "藍", "牛仔", ["百搭"]),
        ("西裝褲", "下身", "黑", "聚酯纖維", ["正式"]),
        ("羊毛大衣", "外套", "駝色", "羊毛", ["優雅"]),
    ]
    for name, cat, col, mat, tags in default_items:
        st.session_state.wardrobe.append(ClothingItem(name, cat, col, mat, tags))

def get_items_by_weather(temp):
    suitable_items = []
    for item in st.session_state.wardrobe:
        is_suitable = False
        # 簡易邏輯
        if temp >= 28: # 熱
            if item.material in ["棉", "麻", "雪紡", "排汗", "聚酯纖維", "牛仔"]: is_suitable = True
            if item.category == "外套": is_suitable = False
        elif 20 <= temp < 28: # 舒適
            is_suitable = True
            if item.material in ["羽絨", "刷毛"]: is_suitable = False
        elif 15 <= temp < 20: # 涼
            is_suitable = True
            if item.material in ["麻", "雪紡"]: is_suitable = False
        else: # 冷
            if item.material in ["羊毛", "羽絨", "刷毛", "皮革", "牛仔", "棉"]: is_suitable = True
            if item.material in ["麻", "雪紡"]: is_suitable = False
        
        if is_suitable:
            suitable_items.append(item)
    return suitable_items

def search_similar(query):
    found = []
    for item in st.session_state.wardrobe:
        if (query in item.name) or (item.name in query) or (item.category in query):
            found.append(item)
    return found

# ==========================================
# 網頁介面 (UI)
# ==========================================

st.title("👕 AI 智能衣櫃助手")
st.markdown("你的個人穿搭顧問，解決「今天穿什麼」的煩惱！")

# --- 側邊欄：新增衣物 ---
st.sidebar.header("➕ 新增衣物")
with st.sidebar.form("add_item_form"):
    new_name = st.text_input("衣物名稱 (如: 黑色帽T)")
    new_cat = st.selectbox("類別", ["上衣", "下身", "外套", "飾品", "鞋子"])
    new_mat = st.selectbox("主要材質", ["棉", "麻", "牛仔", "羊毛", "聚酯纖維", "羽絨", "皮革"])
    new_color = st.text_input("顏色")
    submitted = st.form_submit_button("加入衣櫃")
    
    if submitted and new_name:
        item = ClothingItem(new_name, new_cat, new_color, new_mat, ["自訂"])
        st.session_state.wardrobe.append(item)
        st.sidebar.success(f"已加入：{new_name}")

# --- 主畫面分頁 ---
tab1, tab2, tab3 = st.tabs(["📅 今日穿搭", "🛍️ 購物建議", "🗄️ 我的衣櫃"])

with tab1:
    st.subheader("根據天氣推薦穿搭")
    temp = st.slider("現在氣溫幾度？(°C)", 0, 40, 25)
    
    if st.button("生成搭配"):
        suitable = get_items_by_weather(temp)
        tops = [i for i in suitable if i.category == "上衣"]
        bottoms = [i for i in suitable if i.category == "下身"]
        outers = [i for i in suitable if i.category == "外套"]
        
        if tops and bottoms:
            top = random.choice(tops)
            bottom = random.choice(bottoms)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**上身**\n\n{top.name}\n({top.material})")
            with col2:
                st.info(f"**下身**\n\n{bottom.name}\n({bottom.material})")
                
            if outers and temp < 20:
                outer = random.choice(outers)
                st.warning(f"🧥 **建議外套**：{outer.name}")
                
            st.success("✨ 搭配完成！適合今日天氣。")
        else:
            st.error("❌ 衣櫃存貨不足，無法組成完整搭配。")

with tab2:
    st.subheader("購物小幫手")
    search_query = st.text_input("你想買什麼？(例如：白色T恤)")
    
    if search_query:
        results = search_similar(search_query)
        if results:
            st.warning(f"⚠️ 等等！你的衣櫃已經有 {len(results)} 件類似單品了：")
            for item in results:
                st.write(f"- {item.name} ({item.color}, {item.material})")
        else:
            st.success("✅ 衣櫃裡沒有類似款，這是不錯的新增選擇！")

with tab3:
    st.subheader(f"目前共有 {len(st.session_state.wardrobe)} 件衣物")
    # 顯示所有衣物
    for i, item in enumerate(st.session_state.wardrobe):
        st.text(f"{i+1}. [{item.category}] {item.name} - {item.material}")