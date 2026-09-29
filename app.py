import streamlit as st
import requests
import pandas as pd
import numpy as np
from collections import Counter
import math

st.set_page_config(page_title="数据分析彩票预测助手", layout="wide", page_icon="🎲")

st.title("🎲 彩票历史数据分析与预测系统")
st.caption("注：本系统仅供数据分析与娱乐学习使用，彩票摇号属于独立随机事件，请理性购彩。")

# 1. 彩种规则配置
LOTTERY_RULES = {
    "双色球": {
        "red_total": 33, "red_select": 6, 
        "blue_total": 16, "blue_select": 1,
        "combinations": math.comb(33, 6) * math.comb(16, 1),
        "code": "ssq"
    },
    "超级大乐透": {
        "red_total": 35, "red_select": 5, 
        "blue_total": 12, "blue_select": 2,
        "combinations": math.comb(35, 5) * math.comb(12, 2),
        "code": "dlt"
    },
    "福彩3D": {
        "range": (0, 9), "select": 3,
        "combinations": 10**3,
        "code": "fc3d"
    },
    "香港六合彩特码": {
        "total": 49, "select": 1,
        "combinations": 49,
        "code": "hk6"
    }
}

# 2. 从 API 获取数据
@st.cache_data(ttl=1800)
def fetch_recent_history(lottery_name, fetch_count=20):
    lottery_code = LOTTERY_RULES[lottery_name]["code"]
    url = f"https://www.mxnzp.com/api/lottery/common/history?code={lottery_code}&page=1"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "app_id": "oppoim19e7kxgvg8",
        "app_secret": "VGtwV0x0aGRyNHl0WFFRclU2L0dIQT09"
    }
    
    parsed_history = []
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("code") == 1 and "data" in res_json:
                data_list = res_json["data"][:fetch_count]
                for item in data_list:
                    issue = item.get("expect", "未知期号")
                    open_code = item.get("openCode", "")
                    
                    if lottery_name == "双色球":
                        if "+" in open_code:
                            red_str, blue_str = open_code.split("+")
                            reds = [int(x) for x in red_str.split(",") if x.strip()]
                            blues = [int(x) for x in blue_str.split(",") if x.strip()]
                        else:
                            parts = [int(x) for x in open_code.split(",") if x.strip()]
                            reds, blues = parts[:6], parts[6:]
                        parsed_history.append({"期号": issue, "红球": reds, "蓝球": blues})

                    elif lottery_name == "超级大乐透":
                        if "+" in open_code:
                            red_str, blue_str = open_code.split("+")
                            reds = [int(x) for x in red_str.split(",") if x.strip()]
                            blues = [int(x) for x in blue_str.split(",") if x.strip()]
                        else:
                            parts = [int(x) for x in open_code.split(",") if x.strip()]
                            reds, blues = parts[:5], parts[5:]
                        parsed_history.append({"期号": issue, "前区": reds, "后区": blues})

                    elif lottery_name == "福彩3D":
                        nums = [int(x) for x in open_code.replace(" ", "").split(",") if x.strip()]
                        parsed_history.append({"期号": issue, "开奖号码": nums})

                    elif lottery_name == "香港六合彩特码":
                        parts = [int(x) for x in open_code.split(",") if x.strip()]
                        special = [parts[-1]] if parts else [0]
                        parsed_history.append({"期号": issue, "特码": special})
    except Exception as e:
        st.warning(f"⚠️ API 实时数据获取受限，已自动启用备用模拟数据分析。（{e}）")

    if not parsed_history:
        np.random.seed(42)
        for i in range(fetch_count, 0, -1):
            issue = f"20260{fetch_count-i+1:02d}"
            if lottery_name == "双色球":
                reds = sorted(np.random.choice(range(1, 34), 6, replace=False).tolist())
                blues = [np.random.randint(1, 17)]
                parsed_history.append({"期号": issue, "红球": reds, "蓝球": blues})
            elif lottery_name == "超级大乐透":
                reds = sorted(np.random.choice(range(1, 36), 5, replace=False).tolist())
                blues = sorted(np.random.choice(range(1, 13), 2, replace=False).tolist())
                parsed_history.append({"期号": issue, "前区": reds, "后区": blues})
            elif lottery_name == "福彩3D":
                nums = np.random.randint(0, 10, 3).tolist()
                parsed_history.append({"期号": issue, "开奖号码": nums})
            elif lottery_name == "香港六合彩特码":
                special = [np.random.randint(1, 50)]
                parsed_history.append({"期号": issue, "特码": special})

    return parsed_history

# 3. 计算频次与遗漏值
def analyze_omission_and_frequency(df_history, column_key, total_numbers, is_zero_indexed=False):
    min_num = 0 if is_zero_indexed else 1
    max_num = total_numbers - 1 if is_zero_indexed else total_numbers
    
    counts = {num: 0 for num in range(min_num, max_num + 1)}
    omissions = {num: 0 for num in range(min_num, max_num + 1)}
    
    records = df_history[column_key].tolist()[::-1]
    
    for row in records:
        row_set = set(row)
        for num in range(min_num, max_num + 1):
            if num in row_set:
                counts[num] += 1
                omissions[num] = 0
            else:
                omissions[num] += 1
                
    return counts, omissions

# 4. 侧边栏设置
st.sidebar.header("⚙️ 参数设置")
selected_lottery = st.sidebar.selectbox("选择彩票种类", list(LOTTERY_RULES.keys()))
sample_size = st.sidebar.slider("分析历史期数样本量", min_value=10, max_value=30, value=20, step=5)

confirm_button = st.sidebar.button("🚀 运行分析与可视化", type="primary", use_container_width=True)

if "current_lottery" not in st.session_state:
    st.session_state["current_lottery"] = None

if confirm_button:
    st.session_state["current_lottery"] = selected_lottery

active_lottery = st.session_state["current_lottery"]

if active_lottery is None:
    st.info("👈 请在左侧边栏选择彩票种类并设置参数，然后点击【运行分析与可视化】。")
else:
    rule = LOTTERY_RULES[active_lottery]

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 理论中奖概率")
    jackpot_prob = (1 / rule["combinations"]) * 100
    st.sidebar.write(f"**当前分析彩种：** {active_lottery}")
    st.sidebar.write(f"**单注头奖概率：** `{jackpot_prob:.8f}%`")

    # 5. 主界面内容
    st.subheader(f"📌 {active_lottery} - 近 {sample_size} 期开奖记录")
    
    with st.spinner("正在抓取数据并绘制可视化图表..."):
        history_data = fetch_recent_history(active_lottery, fetch_count=sample_size)
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 号码频次（热度）与遗漏值（冷度）直方图")

    if active_lottery in ["双色球", "超级大乐透"]:
        main_key = "红球" if "红球" in df_history.columns else "前区"
        sub_key = "蓝球" if "蓝球" in df_history.columns else "后区"
        
        main_counts, main_omissions = analyze_omission_and_frequency(df_history, main_key, rule["red_total"])
        sub_counts, sub_omissions = analyze_omission_and_frequency(df_history, sub_key, rule["blue_total"])

        # 转换为 DataFrame 用于图表展示
        df_main = pd.DataFrame({
            "号码": [f"{i:02d}" for i in main_counts.keys()],
            "出现次数(热号)": list(main_counts.values()),
            "当前遗漏(冷号)": list(main_omissions.values())
        }).set_index("号码")

        st.write(f"#### 🔴 {main_key} 冷热频次分布")
        st.bar_chart(df_main)

        df_sub = pd.DataFrame({
            "号码": [f"{i:02d}" for i in sub_counts.keys()],
            "出现次数(热号)": list(sub_counts.values()),
            "当前遗漏(冷号)": list(sub_omissions.values())
        }).set_index("号码")

        st.write(f"#### 🔵 {sub_key} 冷热频次分布")
        st.bar_chart(df_sub)

        # 算法预测逻辑
        hot_main = sorted(main_counts.keys(), key=lambda x: main_counts[x], reverse=True)
        cold_main = sorted(main_omissions.keys(), key=lambda x: main_omissions[x], reverse=True)
        hot_count = max(1, math.ceil(rule["red_select"] * 0.7))
        
        picked_main = set(hot_main[:hot_count])
        for num in cold_main:
            if len(picked_main) < rule["red_select"]:
                picked_main.add(num)

        hot_sub = sorted(sub_counts.keys(), key=lambda x: sub_counts[x], reverse=True)
        cold_sub = sorted(sub_omissions.keys(), key=lambda x: sub_omissions[x], reverse=True)
        picked_sub = {hot_sub[0]}
        if rule["blue_select"] > 1:
            for num in cold_sub:
                if num not in picked_sub:
                    picked_sub.add(num)
                    break

        st.markdown("---")
        st.subheader("🔮 冷热结合 (70% 热号 + 30% 冷号) 预测结果")
        st.success(f"🎯 **预测推荐：** {main_key}: `{sorted(list(picked_main))}` | {sub_key}: `{sorted(list(picked_sub))}`")

    elif active_lottery == "福彩3D":
        counts, omissions = analyze_omission_and_frequency(df_history, "开奖号码", 10, is_zero_indexed=True)
        df_chart = pd.DataFrame({
            "数字": [str(i) for i in counts.keys()],
            "出现次数(热号)": list(counts.values()),
            "当前遗漏(冷号)": list(omissions.values())
        }).set_index("数字")

        st.bar_chart(df_chart)

        hot_nums = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
        cold_nums = sorted(omissions.keys(), key=lambda x: omissions[x], reverse=True)
        picked = [hot_nums[0], hot_nums[1], cold_nums[0]]

        st.markdown("---")
        st.subheader("🔮 预测结果")
        st.success(f"🎯 **预测推荐（2热+1冷组合）：** `{picked}`")

    elif active_lottery == "香港六合彩特码":
        counts, omissions = analyze_omission_and_frequency(df_history, "特码", 49)
        df_chart = pd.DataFrame({
            "特码": [f"{i:02d}" for i in counts.keys()],
            "出现次数(热号)": list(counts.values()),
            "当前遗漏(冷号)": list(omissions.values())
        }).set_index("特码")

        st.bar_chart(df_chart)

        hot_nums = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
        cold_nums = sorted(omissions.keys(), key=lambda x: omissions[x], reverse=True)

        st.markdown("---")
        st.subheader("🔮 预测结果")
        st.success(f"🎯 **推荐下期参考特码（热号+遗漏冷号）：** `{hot_nums[0]:02d}, {cold_nums[0]:02d}`")

    st.info(f"💡 **提示：** 单注头奖理论中奖概率依然为 **{jackpot_prob:.8f}%**。")
