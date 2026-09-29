import math
import requests
import numpy as np
import pandas as pd
import streamlit as st

# 页面基础配置
st.set_page_config(page_title="彩票数据分析平台", layout="wide", page_icon="🎲")

st.title("🎲 彩票历史数据分析与预测平台")
st.caption("注：本系统仅供数据分析与娱乐学习使用，彩票摇号属于独立随机事件，请理性购彩。")

# 侧边栏交互
st.sidebar.header("⚙️ 参数设置")
selected_name = st.sidebar.selectbox("选择彩种", ["双色球", "超级大乐透", "福彩3D", "香港六合彩特码"])
sample_size = st.sidebar.slider("分析期数样本量", min_value=10, max_value=50, value=20, step=5)
run_btn = st.sidebar.button("🚀 运行混合引擎分析", type="primary", use_container_width=True)

# 基础规则计算
def get_rule_info(name):
    if name == "双色球":
        return {"code": "ssq", "p_total": 33, "p_select": 6, "s_total": 16, "s_select": 1, "comb": math.comb(33, 6) * math.comb(16, 1), "zero": False}
    elif name == "超级大乐透":
        return {"code": "dlt", "p_total": 35, "p_select": 5, "s_total": 12, "s_select": 2, "comb": math.comb(35, 5) * math.comb(12, 2), "zero": False}
    elif name == "福彩3D":
        return {"code": "fc3d", "p_total": 10, "p_select": 3, "s_total": 0, "s_select": 0, "comb": 1000, "zero": True}
    else:
        return {"code": "hk6", "p_total": 49, "p_select": 1, "s_total": 0, "s_select": 0, "comb": 49, "zero": False}

rule = get_rule_info(selected_name)

# 侧边栏概率展示
st.sidebar.markdown("---")
st.sidebar.subheader("📊 数学概率分析")
st.sidebar.write(f"**头奖总组合数：** {rule['comb']:,} 种")
st.sidebar.write(f"**单注头奖概率：** `{(1 / rule['comb']) * 100:.8f}%`")

# 带日志诊断的数据获取函数
def fetch_lottery_data(name, count):
    current_rule = get_rule_info(name)
    app_id = st.secrets.get("API_APP_ID", "oppoim19e7kxgvg8")
    app_secret = st.secrets.get("API_APP_SECRET", "VGtwV0x0aGRyNHl0WFFRclU2L0dIQT09")
    
    url = "https://www.mxnzp.com/api/lottery/common/history"
    headers = {"User-Agent": "Mozilla/5.0", "app_id": app_id, "app_secret": app_secret}
    params = {"code": current_rule["code"], "page": 1}
    
    records = []
    log_msg = ""
    is_real_api = False

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=4)
        if resp.status_code == 200:
            res_json = resp.json()
            if res_json.get("code") == 1 and "data" in res_json:
                for item in res_json["data"][:count]:
                    issue = str(item.get("expect", "N/A"))
                    code_str = str(item.get("openCode", "")).replace(" ", "")
                    
                    # 解析号码
                    p_nums, s_nums = [], []
                    if "+" in code_str:
                        p_part, s_part = code_str.split("+")
                        p_nums = [int(x) for x in p_part.split(",") if x.isdigit()]
                        s_nums = [int(x) for x in s_part.split(",") if x.isdigit()]
                    else:
                        parts = [int(x) for x in code_str.split(",") if x.isdigit()]
                        split_idx = 6 if name == "双色球" else (5 if name == "超级大乐透" else len(parts))
                        p_nums = parts[:split_idx]
                        s_nums = parts[split_idx:]
                        
                    records.append({"issue": issue, "p": sorted(p_nums), "s": sorted(s_nums)})
                
                if records:
                    is_real_api = True
                    log_msg = f"🟢 API 调用成功！已成功抓取网络最新 {len(records)} 期【{name}】真实开奖数据。"
            else:
                log_msg = f"🟡 API 返回业务异常信息: {res_json.get('msg', '未知错误')}。已自动切换为本地离线引擎模式。"
        else:
            log_msg = f"🟡 API 网络响应状态码异常: {resp.status_code}。已自动切换为本地离线引擎模式。"
    except Exception as e:
        log_msg = f"🟡 API 请求超时或网络连接失败（原因: {str(e)}）。已自动切换为本地离线引擎模式。"

    # 若 API 请求未成功获得数据，生成本地降级数据
    if not records:
        np.random.seed(999)
        for i in range(count, 0, -1):
            issue_str = f"20260{count - i + 1:02d}"
            p_start = 0 if current_rule["zero"] else 1
            p_range = list(range(p_start, current_rule["p_total"] + (0 if current_rule["zero"] else 1)))
            p_draw = sorted(np.random.choice(p_range, current_rule["p_select"], replace=False).tolist())
            
            s_draw = []
            if current_rule["s_select"] > 0:
                s_range = list(range(1, current_rule["s_total"] + 1))
                s_draw = sorted(np.random.choice(s_range, current_rule["s_select"], replace=False).tolist())
            records.append({"issue": issue_str, "p": p_draw, "s": s_draw})
            
    return records, log_msg, is_real_api

# 核心计算与渲染
if not run_btn:
    st.info("👈 请在左侧选择参数后点击【运行混合引擎分析】开始。")
else:
    with st.spinner("数据处理中..."):
        data_list, api_log, is_real = fetch_lottery_data(selected_name, sample_size)
        
        # 打印数据源诊断日志
        if is_real:
            st.toast(api_log, icon="✅")
            st.caption(f"📡 **数据链接状态：** {api_log}")
        else:
            st.toast(api_log, icon="⚠️")
            st.warning(f"📡 **数据链接日志：** {api_log}")

        # 统计数据计算
        p_start = 0 if rule["zero"] else 1
        p_end = rule["p_total"] - 1 if rule["zero"] else rule["p_total"]
        
        p_counts = {i: 0 for i in range(p_start, p_end + 1)}
        p_omits = {i: 0 for i in range(p_start, p_end + 1)}
        
        for item in reversed(data_list):
            p_set = set(item["p"])
            for num in range(p_start, p_end + 1):
                if num in p_set:
                    p_counts[num] += 1
                    p_omits[num] = 0
                else:
                    p_omits[num] += 1

        s_counts, s_omits = {}, {}
        if rule["s_select"] > 0:
            s_counts = {i: 0 for i in range(1, rule["s_total"] + 1)}
            s_omits = {i: 0 for i in range(1, rule["s_total"] + 1)}
            for item in reversed(data_list):
                s_set = set(item["s"])
                for num in range(1, rule["s_total"] + 1):
                    if num in s_set:
                        s_counts[num] += 1
                        s_omits[num] = 0
                    else:
                        s_omits[num] += 1

        # 算法推荐计算 (70% 热号 + 30% 冷号)
        hot_p = sorted(p_counts.keys(), key=lambda x: p_counts[x], reverse=True)
        cold_p = sorted(p_omits.keys(), key=lambda x: p_omits[x], reverse=True)
        
        need_hot = max(1, math.ceil(rule["p_select"] * 0.7))
        pred_p = set(hot_p[:need_hot])
        for n in cold_p:
            if len(pred_p) < rule["p_select"]:
                pred_p.add(n)
                
        pred_s = []
        if rule["s_select"] > 0:
            hot_s = sorted(s_counts.keys(), key=lambda x: s_counts[x], reverse=True)
            cold_s = sorted(s_omits.keys(), key=lambda x: s_omits[x], reverse=True)
            picked_s = {hot_s[0]}
            if rule["s_select"] > 1:
                for n in cold_s:
                    if n not in picked_s:
                        picked_s.add(n)
                        break
            pred_s = sorted(list(picked_s))

        # ==========================================
        # 页面组件按顺序渲染
        # ==========================================

        # 【位置 1】：算法推荐输出（置顶）
        st.subheader("🔮 70% 热号 + 30% 冷号 算法推荐")
        result_msg = f"**主区号码：** `{sorted(list(pred_p))}`"
        if pred_s:
            result_msg += f" | **副区号码：** `{pred_s}`"
        st.success(f"🎯 {result_msg}")
        st.info(f"💡 分析基于近 {len(data_list)} 期样本。单注头奖理论概率：{(1 / rule['comb']) * 100:.8f}%。")

        st.markdown("---")

        # 【位置 2】：近期数据明细表格
        st.subheader(f"📌 {selected_name} - 近 {len(data_list)} 期数据明细")
        table_df = pd.DataFrame([{
            "期号": item["issue"],
            "主区号码": str(item["p"]),
            "副区号码": str(item["s"]) if item["s"] else "-"
        } for item in data_list])
        st.dataframe(table_df, use_container_width=True)

        st.markdown("---")

        # 【位置 3】：统计特征直方图与副区分布（位于最后端）
        st.subheader("📊 统计特征直方图")
        
        df_p_chart = pd.DataFrame({
            "号码": [f"{i:02d}" for i in p_counts.keys()],
            "出现频次 (热度)": list(p_counts.values()),
            "遗漏期数 (冷度)": list(p_omits.values())
        }).set_index("号码")
        st.write("#### 🔴 主区冷热分布")
        st.bar_chart(df_p_chart)

        if rule["s_select"] > 0:
            df_s_chart = pd.DataFrame({
                "号码": [f"{i:02d}" for i in s_counts.keys()],
                "出现频次 (热度)": list(s_counts.values()),
                "遗漏期数 (冷度)": list(s_omits.values())
            }).set_index("号码")
            st.write("#### 🔵 副区冷热分布")
            st.bar_chart(df_s_chart)
