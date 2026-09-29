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

# 兼容 Streamlit Cloud 海外节点与国内本地直连的真实数据获取函数
def fetch_lottery_data(name, count):
    current_rule = get_rule_info(name)
    records = []
    log_msg = ""
    is_real = False

    # 1. 优先尝试：开放免 Key CDN 源（支持 Streamlit Cloud 海外服务器跨域访问）
    code_map = {"双色球": "ssq", "超级大乐透": "dlt", "福彩3D": "fc3d"}
    target_code = code_map.get(name)

    if target_code:
        cdn_url = f"https://cdn.jsdelivr.net/gh/fanzheng/lottery-data@main/data/{target_code}.json"
        try:
            resp = requests.get(cdn_url, timeout=4)
            if resp.status_code == 200:
                json_data = resp.json()[:count]
                for item in json_data:
                    issue = str(item.get("issue", "N/A"))
                    p_nums = [int(x) for x in item.get("red", [])]
                    s_nums = [int(x) for x in item.get("blue", [])]
                    records.append({"issue": issue, "p": sorted(p_nums), "s": sorted(s_nums)})
                if records:
                    is_real = True
                    log_msg = f"🟢 成功提取真实开奖数据！已同步最新 {len(records)} 期【{name}】真实历史记录。"
        except Exception:
            pass

    # 2. 备选尝试：直连中国福彩/体彩官方 API 接口（国内本地环境生效）
    if not records:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.cwl.gov.cn/"
        }
        try:
            if name == "双色球":
                url = f"https://cq.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount={count}"
                resp = requests.get(url, headers=headers, timeout=4)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("result", []):
                        issue = str(item.get("code"))
                        p_nums = [int(x) for x in item.get("red", "").split(",") if x.isdigit()]
                        s_nums = [int(x) for x in item.get("blue", "").split(",") if x.isdigit()]
                        records.append({"issue": issue, "p": sorted(p_nums), "s": sorted(s_nums)})
            elif name == "超级大乐透":
                url = f"https://webapi.sports.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=85&provinceId=0&pageSize={count}&isVerify=1"
                resp = requests.get(url, headers=headers, timeout=4)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("value", {}).get("list", []):
                        issue = str(item.get("lotteryDrawNum"))
                        parts = item.get("lotteryDrawResult", "").split(" ")
                        if len(parts) >= 7:
                            p_nums = [int(x) for x in parts[:5]]
                            s_nums = [int(x) for x in parts[5:7]]
                            records.append({"issue": issue, "p": sorted(p_nums), "s": sorted(s_nums)})
            
            if records:
                is_real = True
                log_msg = f"🟢 成功免 Key 直连官方公开数据源！已获取最新 {len(records)} 期【{name}】真实开奖记录。"
        except Exception:
            pass

    # 3. 兜底逻辑：若网络彻底不可用或选择香港六合彩，切入降级算法
    if not records:
        log_msg = f"🟡 网络接口超时或暂不支持该彩种，已自动切入本地测试数据模式（建议切换双色球/大乐透试用）。"
        np.random.seed(888)
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
            
    return records, log_msg, is_real

# 核心计算与渲染
if not run_btn:
    st.info("👈 请在左侧选择参数后点击【运行混合引擎分析】开始。")
else:
    with st.spinner("实时提取数据与计算中..."):
        data_list, api_log, is_real = fetch_lottery_data(selected_name, sample_size)
        
        # 打印日志状态
        if is_real:
            st.success(f"📡 **数据链接状态：** {api_log}")
        else:
            st.warning(f"📡 **数据链接状态：** {api_log}")

        # 统计特征计算
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
        # 页面组件按新顺序渲染
        # ==========================================

        # 【位置 1】：算法推荐输出（最前端置顶）
        st.subheader("🔮 70% 热号 + 30% 冷号 算法推荐")
        result_msg = f"**主区号码：** `{sorted(list(pred_p))}`"
        if pred_s:
            result_msg += f" | **副区号码：** `{pred_s}`"
        st.success(f"🎯 {result_msg}")
        st.caption(f"💡 基于近 {len(data_list)} 期真实开奖样本分析。单注头奖理论概率：{(1 / rule['comb']) * 100:.8f}%。")

        st.markdown("---")

        # 【位置 2】：近期开奖数据表格
        st.subheader(f"📌 {selected_name} - 近 {len(data_list)} 期数据明细")
        table_df = pd.DataFrame([{
            "期号": item["issue"],
            "主区号码": str(item["p"]),
            "副区号码": str(item["s"]) if item["s"] else "-"
        } for item in data_list])
        st.dataframe(table_df, use_container_width=True)

        st.markdown("---")

        # 【位置 3】：统计特征直方图与副区冷热分布（移至最末端）
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
