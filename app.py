import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import base64

# ==================== 1. 页面基本配置 ====================
st.set_page_config(page_title="理财管家 - 消费管理系统", layout="wide")

# ==================== 2. Session 状态初始化 ====================
if "user_income" not in st.session_state:
    st.session_state.user_income = 3000.0
if "fixed_expense" not in st.session_state:
    st.session_state.fixed_expense = 500.0
if "target_savings" not in st.session_state:
    st.session_state.target_savings = 300.0

if "user_personality" not in st.session_state:
    st.session_state.user_personality = "未测评 (通用理性型)"

if "in_quiz_mode" not in st.session_state:
    st.session_state.in_quiz_mode = False
if "quiz_step" not in st.session_state:
    st.session_state.quiz_step = 1
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "ledger_records" not in st.session_state:
    st.session_state.ledger_records = pd.DataFrame(
        columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家专业建议"]
    )

# ==================== 3. 消费人格数据库与 15 题题库 ====================
PERSONALITY_PROFILES = {
    "脉冲体验者": {
        "desc": "极易被新鲜感与情绪驱动，为即时快乐买单，资金留存率偏低。",
        "advice_rule": "拦截建议：启动 72 小时冷静期！3天后依然想买再决定，通常可拦截 80% 冲动支出。"
    },
    "沉浸品质家": {
        "desc": "追求质感与深度体验，不在意数量，单笔开销大，现金流易阶段性波动。",
        "advice_rule": "诊断提示：请评估预估使用次数并计算单次使用成本，评估是否符合品质基金配额。"
    },
    "策略精算师": {
        "desc": "极致比价，精通规则与凑单，享受优惠带来的掌控感，需防范凑单陷阱。",
        "advice_rule": "诊断提示：核查是否存在为了凑满减而购买非刚需商品的情况，注意计算付出研究的时间成本。"
    },
    "安稳守恒者": {
        "desc": "风险偏好极低，奉行非必要不支出，储蓄安全感极强，资金抗通胀率较低。",
        "advice_rule": "诊断提示：开销极为克制。刚需消费建议一步到位购买高质量耐用品，降低长期维护损耗。"
    },
    "社交随浪者": {
        "desc": "消费易受社交圈、人情及外界评价影响，被动与社交性支出偏高。",
        "advice_rule": "诊断提示：请关注人际社交预算上限，月末复盘评估该笔社交的实际投资回报率。"
    },
    "宏观规划家": {
        "desc": "极度理性自律，每笔开销都服务于长远财务目标与既定预算。",
        "advice_rule": "诊断提示：支出符合既定财务规划，未偏离月度控制线，整体资产管理状况极为稳健。"
    }
}

QUESTIONS_DB = [
    {
        "id": "Q1",
        "title": "连续加班一周后的周末，你最倾向于用哪种方式放松？",
        "options": {
            "A": "大餐或买下购物车里搁置很久的衣服",
            "B": "预约高档SPA、看演出或高品质微度假",
            "C": "寻找划算的小吃团购或免费的公园展览",
            "D": "宅在家里做饭、追剧、打扫卫生，零支出"
        },
        "weights": {"A": {"E":2, "I":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q2",
        "title": "在电商大促期间，你的典型状态是？",
        "options": {
            "A": "看到直播间促销就忍不住下单",
            "B": "只买看好的大牌耐用品或提升生活质量的大件",
            "C": "计算跨店满减与消费券，拿到最低价",
            "D": "基本不关注，手头的东西没坏就不买"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "P":2}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q3",
        "title": "朋友约你吃人均消费超出平时预算的餐厅，你会？",
        "options": {
            "A": "答应前往，认为大家开心最重要",
            "B": "欣然前往，如果品质好就觉得很值得",
            "C": "搜寻各大平台是否有优惠券或代金券",
            "D": "婉拒或建议更换性价比更高的地方"
        },
        "weights": {"A": {"S":2, "I":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q4",
        "title": "购买高频使用的电子产品时，你的决策核心是？",
        "options": {
            "A": "外观好看、功能炫酷，有新出的款式就想买",
            "B": "顶级配置、极佳体验与售后服务",
            "C": "挑选很久，找到补贴叠加满减后的最低价",
            "D": "性能满足未来3-5年使用，绝不出预算"
        },
        "weights": {"A": {"E":2, "I":1}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q5",
        "title": "看到一件不在计划内但很喜欢的物件，你会？",
        "options": {
            "A": "根据即时喜好直接购买",
            "B": "评估品质与设计，高品质则考虑购买",
            "C": "搜索同款，寻找更便宜的渠道",
            "D": "提醒自己非刚需，冷静离开"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q6",
        "title": "对各类会员订阅的态度是？",
        "options": {
            "A": "按需开通，包含许多自动续费",
            "B": "只购买高频使用的顶级体验服务",
            "C": "等待拼单、联合赠送或首优惠时开通",
            "D": "能用免费版的不付费，极少开通订阅"
        },
        "weights": {"A": {"I":2, "E":1}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q7",
        "title": "查看上个月的账单时，你的第一反应通常是？",
        "options": {
            "A": "关注资金去向，感觉超出预期",
            "B": "认为获得了相符的产品与体验",
            "C": "评估优惠省下的金额，关注性价比",
            "D": "确认在预算控制内，转入理财账户"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q8",
        "title": "关于日常储蓄与理财，你目前的真实习惯是？",
        "options": {
            "A": "发工资后先支出，月末有剩余才储蓄",
            "B": "储蓄用于下一次大额品质消费",
            "C": "研究稳健理财与高息存款",
            "D": "严格执行强制储蓄，按比例划转"
        },
        "weights": {"A": {"I":2, "E":1}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":2}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q9",
        "title": "如果突然获得一笔计划外资金，你会？",
        "options": {
            "A": "用于旅行或心仪已久的商品",
            "B": "升级日常生活用品品质",
            "C": "大部分存入，小部分购买刚需",
            "D": "全部转入储蓄或投资账户"
        },
        "weights": {"A": {"E":2, "I":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "F":1}, "D": {"F":2, "P":2}}
    },
    {
        "id": "Q10",
        "title": "面对促销活动，你常做的是？",
        "options": {
            "A": "为了凑满减加购非计划商品",
            "B": "凑单商品符合品质要求时顺便参与",
            "C": "计算折后单价或寻找拼单",
            "D": "保持警惕，不购买不需要的物品"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q11",
        "title": "在处理闲置旧物时，你一般会？",
        "options": {
            "A": "暂时堆放或直接处理",
            "B": "赠送他人或回收处理",
            "C": "整理挂二手平台转让变现",
            "D": "尽量使用至损耗上限，少淘汰旧物"
        },
        "weights": {"A": {"I":1, "E":1}, "B": {"S":1, "Q":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q12",
        "title": "临近月末预算紧张时，你会怎么应对？",
        "options": {
            "A": "适度控制，使用信用支付补充",
            "B": "减少非必要社交，维持基础饮食品质",
            "C": "调整为低消费模式，自行做饭",
            "D": "严格按月度规划执行，很少出现该情况"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "F":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q13",
        "title": "对于流行单品或网红体验，你的态度是？",
        "options": {
            "A": "感兴趣并愿意前往体验",
            "B": "具备高品质或独特价值时前往",
            "C": "关注后续折扣或优惠时段体验",
            "D": "不跟风消费，按自身规划支出"
        },
        "weights": {"A": {"E":2, "S":1}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q14",
        "title": "你对微小支出的感知是？",
        "options": {
            "A": "平时不太关注，累积后影响整体预算",
            "B": "提高便利度与舒适感的小额支出是合理的",
            "C": "重视小额优惠，尽量使用优惠券",
            "D": "养成良好习惯，规避不必要的微小开销"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q15",
        "title": "你希望消费管理系统主要帮助解决什么问题？",
        "options": {
            "A": "管控冲动支出，提高资金留存",
            "B": "优化非必要开支，保持既有品质",
            "C": "整理优惠与比价，提高资金效率",
            "D": "提供数据分析，辅助长期资产规划"
        },
        "weights": {"A": {"E":2, "I":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    }
]

# ==================== 4. 统一主色调与全局 UI 样式重构 ====================
GLOBAL_CSS = """
<style>
    /* 全局背景色与字体基准 */
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 隐藏 Streamlit 默认页眉页脚 */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }

    /* 主内容容器限制与边距 */
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* 顶部卡片 */
    .title-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .title-card h2 {
        color: #f8fafc;
        margin: 0 0 8px 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .title-card p {
        color: #94a3b8;
        margin: 0;
        font-size: 0.95rem;
    }

    /* 数据指标卡片 */
    .metric-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 18px;
        text-align: left;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-num {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
    }

    /* 表单与输入控件强化（解决选项与背景融合、字体过小问题） */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    div[role="radiogroup"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
        color: #f8fafc !important;
    }

    /* Radio 选项增强设计 */
    div[role="radiogroup"] {
        padding: 16px !important;
        gap: 12px !important;
    }
    div[role="radiogroup"] label {
        background-color: #334155 !important;
        padding: 12px 16px !important;
        border-radius: 6px !important;
        border: 1px solid #475569 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        margin-bottom: 4px !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: #2563eb !important;
        background-color: #1e293b !important;
    }
    div[role="radiogroup"] label p {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: #f8fafc !important;
    }

    /* Input/Select 内部字体大小调整 */
    input, select, textarea {
        font-size: 1rem !important;
        color: #f8fafc !important;
    }
    
    /* 统一按钮样式 */
    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: background-color 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
    }

    /* Sidebar 样式调校 */
    section[data-testid="stSidebar"] {
        background-color: #0b1120 !important;
        border-right: 1px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1 !important;
    }
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ==================== 5. 路由逻辑切换 ====================

# ----------------- 场景 A: 独立全屏测评页面 -----------------
if st.session_state.in_quiz_mode:
    st.markdown("""
    <div class="title-card">
        <h2>消费基因评估系统</h2>
        <p>基于 8 维特征计分法构建，用于生成针对性的省钱诊断逻辑</p>
    </div>
    """, unsafe_allow_html=True)
    
    total_q = len(QUESTIONS_DB)
    curr_step = st.session_state.quiz_step
    
    if curr_step <= total_q:
        q_data = QUESTIONS_DB[curr_step - 1]
        
        st.progress(curr_step / total_q, text=f"评估进度：第 {curr_step} / {total_q} 题")
        
        st.markdown(f"#### {q_data['id']}. {q_data['title']}")
        
        opts = list(q_data["options"].keys())
        selected_opt = st.radio(
            "选择符合实际情况的选项：",
            options=opts,
            format_func=lambda x: f"【选项 {x}】{q_data['options'][x]}",
            key=f"standalone_q_{q_data['id']}"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
        
        with b_col1:
            if curr_step > 1:
                if st.button("上一题", use_container_width=True):
                    st.session_state.quiz_step -= 1
                    st.rerun()
            else:
                if st.button("退出评估", use_container_width=True):
                    st.session_state.in_quiz_mode = False
                    st.rerun()
                    
        with b_col3:
            btn_label = "下一题" if curr_step < total_q else "生成报告"
            if st.button(btn_label, use_container_width=True):
                st.session_state.quiz_answers[q_data['id']] = selected_opt
                st.session_state.quiz_step += 1
                st.rerun()

    else:
        dim_scores = {"E":0, "R":0, "Q":0, "V":0, "I":0, "P":0, "S":0, "F":0}
        
        for q_item in QUESTIONS_DB:
            qid = q_item["id"]
            user_ans = st.session_state.quiz_answers.get(qid)
            if user_ans and user_ans in q_item["weights"]:
                for d_k, d_v in q_item["weights"][user_ans].items():
                    dim_scores[d_k] += d_v
        
        scores = {
            "脉冲体验者": dim_scores["E"] * 1.2 + dim_scores["I"] * 1.2,
            "沉浸品质家": dim_scores["Q"] * 1.5 + dim_scores["R"] * 0.5,
            "策略精算师": dim_scores["V"] * 1.5 + dim_scores["R"] * 0.5,
            "安稳守恒者": dim_scores["F"] * 1.2 + dim_scores["P"] * 1.0,
            "社交随浪者": dim_scores["S"] * 1.5 + dim_scores["E"] * 0.8,
            "宏观规划家": dim_scores["P"] * 1.2 + dim_scores["F"] * 0.8 + dim_scores["R"] * 0.5
        }
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_p, primary_score = sorted_scores[0]
        secondary_p, secondary_score = sorted_scores[1]
        
        has_secondary = (primary_score - secondary_score) / (primary_score + 1e-5) < 0.15
        
        final_personality_str = primary_p
        if has_secondary:
            final_personality_str += f" / {secondary_p}"
            
        st.session_state.user_personality = final_personality_str
        
        st.success(f"评估完成，您的消费倾向定性为：【{final_personality_str}】")
        
        p_info = PERSONALITY_PROFILES.get(primary_p, {})
        st.markdown(f"**画像特征**：{p_info.get('desc')}")
        st.info(f"**核心管控原则**：\n{p_info.get('advice_rule')}")
        
        st.markdown("---")
        st.markdown("#### 维度分布图")
        score_df = pd.DataFrame(list(scores.items()), columns=["人格类型", "得分"]).sort_values(by="得分", ascending=True)
        
        fig_score = px.bar(score_df, x="得分", y="人格类型", orientation='h', color_discrete_sequence=["#2563eb"])
        fig_score.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(color='#f8fafc', size=13),
            xaxis=dict(gridcolor='#334155'),
            yaxis=dict(gridcolor='#334155')
        )
        st.plotly_chart(fig_score, use_container_width=True)
        
        if st.button("保存并返回管理系统", use_container_width=True):
            st.session_state.in_quiz_mode = False
            st.rerun()

# ----------------- 场景 B: 主记账管理页面 -----------------
else:
    with st.sidebar:
        st.markdown("### 财务控制台")
        st.session_state.user_income = st.number_input("每月总收入 (RM)", min_value=0.0, step=100.0, value=st.session_state.user_income)
        st.session_state.fixed_expense = st.number_input("刚性固定支出 (RM)", min_value=0.0, step=50.0, value=st.session_state.fixed_expense)
        st.session_state.target_savings = st.number_input("强制储蓄目标 (RM)", min_value=0.0, step=50.0, value=st.session_state.target_savings)
        
        st.markdown("---")
        st.markdown("### 当前消费人格")
        st.markdown(f"**{st.session_state.user_personality}**")

    monthly_budget = st.session_state.user_income - st.session_state.fixed_expense - st.session_state.target_savings
    spent_so_far = st.session_state.ledger_records["金额(RM)"].sum() if not st.session_state.ledger_records.empty else 0.0
    remaining_budget = monthly_budget - spent_so_far
    daily_safe_spend = max(0.0, round(remaining_budget / 30, 2))
    current_month_str = datetime.now().strftime("%Y-%m")

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(f"""
        <div class="title-card">
            <h2>理财管家 - 消费管理系统</h2>
            <p>结合 【{st.session_state.user_personality}】 匹配专业省钱建议与账单存档</p>
        </div>
        """, unsafe_allow_html=True)
    with head_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("启动消费倾向测评", use_container_width=True):
            st.session_state.in_quiz_mode = True
            st.session_state.quiz_step = 1
            st.session_state.quiz_answers = {}
            st.rerun()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-box"><div class="metric-title">月收入</div><div class="metric-num">RM {st.session_state.user_income:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-box"><div class="metric-title">自由支配预算</div><div class="metric-num">RM {monthly_budget:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-box"><div class="metric-title">已累计支出</div><div class="metric-num" style="color:#f43f5e;">RM {spent_so_far:,.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-box"><div class="metric-title">每日安全额度</div><div class="metric-num" style="color:#38bdf8;">RM {daily_safe_spend:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["智能记账与诊断", "消费特点分析图表", "资金流向与储蓄库"])

    with tab1:
        l_col, r_col = st.columns([1.1, 1.9])
        with l_col:
            st.markdown("#### 录入单笔开销")
            with st.form("input_form", clear_on_submit=True):
                amount = st.number_input("消费金额 (RM)", min_value=0.0, step=5.0)
                category = st.selectbox("消费分类", ["餐饮美食", "交通出行", "弹性享乐", "日用百货", "数码大件", "人情社交", "其他支出"])
                detail = st.text_input("具体明细描述", placeholder="例：办公餐饮 / 日用品采购")
                
                if st.form_submit_button("提交并获取建议", use_container_width=True):
                    if amount > 0:
                        primary_p = st.session_state.user_personality.split(" ")[0]
                        rule = PERSONALITY_PROFILES.get(primary_p, {}).get("advice_rule", f"账单已记录，建议每日额度控制在 RM {daily_safe_spend} 以内。")
                        
                        advice = f"[{primary_p} 诊断] {rule}"
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        new_data = pd.DataFrame([[now_str, current_month_str, amount, category, detail, advice]],
                                                columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家专业建议"])
                        st.session_state.ledger_records = pd.concat([st.session_state.ledger_records, new_data], ignore_index=True)
                        st.success("开销已存档并生成省钱诊断建议。")
                        st.rerun()

        with r_col:
            st.markdown("#### 账单历史存档")
            if not st.session_state.ledger_records.empty:
                st.dataframe(st.session_state.ledger_records.iloc[::-1][["日期", "消费分类", "金额(RM)", "具体明细", "理财管家专业建议"]], use_container_width=True, height=360, hide_index=True)
            else:
                st.info("暂无开销记录。")

    with tab2:
        if not st.session_state.ledger_records.empty:
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 消费分类占比")
                pie_df = st.session_state.ledger_records.groupby("消费分类")["金额(RM)"].sum().reset_index()
                fig_pie = px.pie(pie_df, values="金额(RM)", names="消费分类", hole=0.4, color_discrete_sequence=px.colors.qualitative.Dark24)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'))
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                st.markdown("#### 消费趋势")
                fig_bar = px.bar(st.session_state.ledger_records, x="日期", y="金额(RM)", color="消费分类", color_discrete_sequence=px.colors.qualitative.Dark24)
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#f8fafc'),
                    xaxis=dict(gridcolor='#334155'),
                    yaxis=dict(gridcolor='#334155')
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("暂无数据可供分析。")

    with tab3:
        st.markdown("#### 资产与预估积累")
        st.metric("预估本月积累总额 (含强制储蓄)", f"RM {st.session_state.target_savings + max(0.0, remaining_budget):,.2f}")
