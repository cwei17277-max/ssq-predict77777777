import streamlit as st
import requests
import pandas as pd
import numpy as np
from collections import Counter
import math

st.set_page_config(page_title="数据分析彩票预测助手", layout="wide", page_icon="🎲")

st.title("🎲 彩票历史数据分析与预测系统")
st.caption("注：本系统仅供数据分析与娱乐学习使用，彩票摇号属于独立随机事件，请理性购彩。")

# 1. 彩种规则与 API 标识配置
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

# 2. 从免费公共 API 获取数据并处理 JSON 解析
@st.cache_data(ttl=1800)  # 缓存30分钟，避免过于频繁调用 API
def fetch_recent_history(lottery_name):
    lottery_code = LOTTERY_RULES[lottery_name]["code"]
    
    # 免费开放 API 接口端点 (例: RollToolsApi 公开查询端点)
    url = f"https://www.mxnzp.com/api/lottery/common/history?code={lottery_code}&page=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        # mxnzp 公开测试 app_id/app_secret
        "app_id": "oppoim19e7kxgvg8",
        "app_secret": "VGtwV0x0aGRyNHl0WFFRclU2L0dIQT09"
    }
    
    parsed_history = []
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            # 校验 JSON 返回状态
            if res_json.get("code") == 1 and "data" in res_json:
                data_list = res_json["data"][:10]  # 提取近10期
                
                for item in data_list:
                    issue = item.get("expect", "未知期号")
                    open_code = item.get("openCode", "") # 格式通常为: "01,05,12,19,25,31+08" 或 "1,3,5"
                    
                    # --- 开始解析 JSON 中开奖号码字符串 ---
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
        st.warning(f"⚠️ API 实时数据获取受限或超时，系统已自动启用备用模拟数据分析。（错误信息: {e}）")

    # 兜底机制：如果 API 请求失败或返回空，使用本地生成规范数据，防止应用崩溃
    if not parsed_history:
        np.random.seed(10)
        for i in range(10, 0, -1):
            issue = f"20260{10-i+1:02d}"
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

# 3. 侧边栏及界面设置
selected_lottery = st.sidebar.selectbox("选择彩票种类", list(LOTTERY_RULES.keys()))
rule = LOTTERY_RULES[selected_lottery]

# 侧边栏展示理论概率
st.sidebar.markdown("---")
st.sidebar.subheader("📊 理论中奖概率")
jackpot_prob = (1 / rule["combinations"]) * 100
st.sidebar.write(f"**头奖组合总数：** {rule['combinations']:,} 种")
st.sidebar.write(f"**单注头奖概率：** `{jackpot_prob:.8f}%`")

# 4. 页面主体：加载并显示近 10 期开奖记录
st.subheader(f"📌 {selected_lottery} - 近 10 期开奖记录")
history_data = fetch_recent_history(selected_lottery)
df_history = pd.DataFrame(history_data)
st.dataframe(df_history, use_container_width=True)

# 5. 数据分析与热号预测
st.markdown("---")
st.subheader("🔮 基于频次分析的下一期预测")

if selected_lottery in ["双色球", "超级大乐透"]:
    main_key = "红球" if "红球" in df_history.columns else "前区"
    sub_key = "蓝球" if "蓝球" in df_history.columns else "后区"
    
    # 提取主球与副球频次
    all_main = [num for row in df_history[main_key] for num in row]
    main_counts = Counter(all_main)
    
    all_sub = [num for row in df_history[sub_key] for num in row]
    sub_counts = Counter(all_sub)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**近10期{main_key}热号 TOP 5:**")
        st.write(dict(main_counts.most_common(5)))
    with col2:
        st.write(f"**近10期{sub_key}热号:**")
        st.write(dict(sub_counts.most_common(3)))
        
    # 选取出现频次最高的号码
    top_main = [item[0] for item in main_counts.most_common(rule['red_select'])]
    top_sub = [item[0] for item in sub_counts.most_common(rule['blue_select'])]
    
    # 若频次种类不足，自动补充未出现号码
    while len(top_main) < rule['red_select']:
        for n in range(1, rule['red_total'] + 1):
            if n not in top_main:
                top_main.append(n)
            if len(top_main) == rule['red_select']:
                break
                
    while len(top_sub) < rule['blue_select']:
        for n in range(1, rule['blue_total'] + 1):
            if n not in top_sub:
                top_sub.append(n)
            if len(top_sub) == rule['blue_select']:
                break

    st.success(f"🎯 **预测下期推荐号码：** {main_key}: `{sorted(top_main)}` | {sub_key}: `{sorted(top_sub)}`")

elif selected_lottery == "福彩3D":
    all_nums = [num for row in df_history["开奖号码"] for num in row]
    num_counts = Counter(all_nums)
    top_3 = [item[0] for item in num_counts.most_common(3)]
    st.success(f"🎯 **预测下期推荐百/十/个位高频数字：** `{top_3}`")

elif selected_lottery == "香港六合彩特码":
    all_specials = [row[0] for row in df_history["特码"]]
    counts = Counter(all_specials)
    top_special = counts.most_common(1)[0][0] if counts else 1
    st.success(f"🎯 **预测下期推荐特码（热号）：** `{top_special:02d}`")

# 概率提示
st.info(f"💡 **概率提醒：** 购买上述预测号码 1 注，中头奖的数学概率依然为 **{jackpot_prob:.8f}%**。")