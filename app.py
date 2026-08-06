import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# ==================== 1. 统一高质感浅色 UI (CSS) ====================
st.set_page_config(page_title="PocketSmith AI Ledger", layout="wide", page_icon="💳")

st.markdown("""
<style>
    /* 全局背景：统一暖灰色调 */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 顶部 Banner 统一深蓝高级渐变 */
    .hero-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.15);
    }
    
    /* 统一 Metric 指标卡片 */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    .metric-label {
        font-size: 0.8rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
    }
    .metric-subtext {
        font-size: 0.8rem;
        margin-top: 4px;
    }

    /* 统一浅色表单与表格 */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    
    /* 统一主按钮样式 */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
    }

    /* 统一 Tab 选项卡样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #64748b;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #2563eb !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 2. Session 会话状态初始化 ====================
if "user_income" not in st.session_state:
    st.session_state.user_income = 3000.0
if "fixed_expense" not in st.session_state:
    st.session_state.fixed_expense = 500.0
if "target_savings" not in st.session_state:
    st.session_state.target_savings = 300.0

if "user_personality" not in st.session_state:
    st.session_state.user_personality = "未测评 (通用理性型)"
if "quiz_step" not in st.session_state:
    st.session_state.quiz_step = 0
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "ledger_records" not in st.session_state:
    st.session_state.ledger_records = pd.DataFrame(
        columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家专业建议"]
    )

monthly_budget = st.session_state.user_income - st.session_state.fixed_expense - st.session_state.target_savings
current_month_str = datetime.now().strftime("%Y-%m")

# ==================== 3. 侧边栏：统一浅色参数设置 ====================
with st.sidebar:
    st.markdown("### ⚙️ 个人财务控制台")
    st.caption("设定您的每月预算基准")
    
    st.session_state.user_income = st.number_input(
        "💵 每月总收入 (RM)", min_value=0.0, step=100.0, value=st.session_state.user_income
    )
    st.session_state.fixed_expense = st.number_input(
        "🏠 刚性固定支出 (房租/水电气) (RM)", min_value=0.0, step=50.0, value=st.session_state.fixed_expense
    )
    st.session_state.target_savings = st.number_input(
        "🎯 强制储蓄目标 (RM)", min_value=0.0, step=50.0, value=st.session_state.target_savings
    )
    
    st.markdown("---")
    st.markdown("### 🧬 当前消费特点画像")
    st.info(f"**{st.session_state.user_personality}**")

# ==================== 4. 顶部 Header ====================
st.markdown(f"""
<div class="hero-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="color: white; margin:0; font-size: 1.8rem; font-weight: 800; letter-spacing: 0.5px;">
                PocketSmith 智能消费管理系统
            </h1>
            <p style="color: #dbeafe; margin: 4px 0 0 0; font-size: 0.9rem;">
                专业理财管家 · 实时分析与智能开销存档
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(255, 255, 255, 0.2); color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                统一清爽视觉版
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 计算财务数据
spent_so_far = st.session_state.ledger_records["金额(RM)"].sum() if not st.session_state.ledger_records.empty else 0.0
remaining_budget = monthly_budget - spent_so_far
daily_safe_spend = max(0.0, round(remaining_budget / 30, 2))

# 4大指标卡片
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">月度总收入</div>
        <div class="metric-value" style="color:#0284c7;">RM {st.session_state.user_income:,.2f}</div>
        <div class="metric-subtext" style="color:#64748b;">固定支出: RM {st.session_state.fixed_expense:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">可自由支配预算</div>
        <div class="metric-value">RM {monthly_budget:,.2f}</div>
        <div class="metric-subtext" style="color:#64748b;">预留储蓄: RM {st.session_state.target_savings:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    spent_color = "#dc2626" if spent_so_far > monthly_budget else "#d97706"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">本月已累计支出</div>
        <div class="metric-value" style="color:{spent_color};">RM {spent_so_far:,.2f}</div>
        <div class="metric-subtext" style="color:#64748b;">共记录 {len(st.session_state.ledger_records)} 笔开销</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    rem_color = "#16a34a" if remaining_budget >= 0 else "#dc2626"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">每日安全额度 (Daily Safe)</div>
        <div class="metric-value" style="color:{rem_color};">RM {daily_safe_spend:,.2f}</div>
        <div class="metric-subtext" style="color:{rem_color};">{'预算控制良好' if remaining_budget>=0 else '超支预警'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== 5. 核心 Tab 功能区 ====================
tab_track, tab_analytics, tab_bank, tab_quiz = st.tabs([
    "✍️ 智能记账与开销诊断", 
    "📊 消费特点分析图表", 
    "🏦 资金流向与储蓄库", 
    "🧩 财商心理特点测评"
])

# ----------------- TAB 1: 记账与专业诊断 -----------------
with tab_track:
    left_col, right_col = st.columns([1.1, 1.9])
    
    with left_col:
        st.markdown("### ➕ 录入开销")
        with st.form("expense_input_form", clear_on_submit=True):
            amount = st.number_input("消费金额 (RM)", min_value=0.0, step=5.0, value=0.0)
            category = st.selectbox("消费分类", ["餐饮美食", "交通出行", "弹性享乐(娱乐/社交)", "日用百货", "数码/大件", "其他支出"])
            detail = st.text_input("具体明细 / 场景描述", placeholder="例：星巴克咖啡 / 朋友聚餐")
            
            submit_btn = st.form_submit_button("🚀 存档并获取管家建议", use_container_width=True)
            
            if submit_btn and amount > 0:
                # 专业理财管家建议逻辑
                personality = st.session_state.user_personality
                if "冲动享乐" in personality:
                    if category in ["弹性享乐(娱乐/社交)", "餐饮美食"] and amount > 50:
                        advice = f"💡 管家建议：检测到高额弹性开支 (RM {amount})！冲动型消费易造成预算缺口，建议设 24 小时冷静期。"
                    else:
                        advice = f"🟢 记录成功。请控制每日支出不超过 RM {daily_safe_spend}。"
                elif "焦虑防御" in personality:
                    if category in ["弹性享乐(娱乐/社交)", "餐饮美食"]:
                        advice = f"🟢 管家建议：消费 RM {amount} 属于合理的品质支出，适度放松有助于保持长期健康理财心态。"
                    else:
                        advice = f"🟢 支出符合防线规划，财务状况稳健。"
                elif "目标驱动" in personality:
                    advice = f"🎯 管家建议：已记账 RM {amount}。本月剩余额度 RM {max(0.0, remaining_budget - amount):,.2f}，距储蓄目标更近一步。"
                else:
                    advice = f"🟢 已存档！该笔开销占每日建议额度的 {round((amount/daily_safe_spend)*100, 1) if daily_safe_spend > 0 else 100}%。"
                
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame([[now_str, current_month_str, amount, category, detail, advice]],
                                       columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家专业建议"])
                
                st.session_state.ledger_records = pd.concat([st.session_state.ledger_records, new_row], ignore_index=True)
                st.success("账目已完美存档！")
                st.rerun()

    with right_col:
        st.markdown("### 📜 消费历史流水存档 (Transaction Archive)")
        if not st.session_state.ledger_records.empty:
            display_df = st.session_state.ledger_records.iloc[::-1][["日期", "消费分类", "金额(RM)", "具体明细", "理财管家专业建议"]]
            st.dataframe(display_df, use_container_width=True, height=360, hide_index=True)
        else:
            st.info("💡 当前暂无开销记录。在左侧录入第一笔消费即可开启存档与分析！")

# ----------------- TAB 2: 图表分析 -----------------
with tab_analytics:
    if not st.session_state.ledger_records.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### 🍩 消费领域分布占比")
            cat_summary = st.session_state.ledger_records.groupby("消费分类")["金额(RM)"].sum().reset_index()
            fig_pie = px.pie(cat_summary, values="金额(RM)", names="消费分类", hole=0.55,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#334155'), margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            st.markdown("#### 📈 消费时间分布与开支流向")
            fig_bar = px.bar(st.session_state.ledger_records, x="日期", y="金额(RM)", color="消费分类",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#334155'), xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9'), margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("💡 暂无数据，请先录入消费事项。")

# ----------------- TAB 3: 资金与储蓄库 -----------------
with tab_bank:
    st.markdown("### 🏦 资产与预算结余概览")
    
    vault_balance = st.session_state.target_savings + max(0.0, remaining_budget)
    
    bank_col1, bank_col2 = st.columns([1.1, 1.9])
    with bank_col1:
        st.markdown(f"""
        <div style="background: #ffffff; padding:24px; border-radius:16px; border:1px solid #e2e8f0; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <div style="color:#64748b; font-size:0.8rem; font-weight:600;">ESTIMATED TOTAL SAVINGS</div>
            <div style="color:#2563eb; font-size:0.9rem; margin-top:4px;">预算与储蓄储备账户</div>
            <hr style="border-color:#f1f5f9; margin:15px 0;">
            <div style="color:#64748b; font-size:0.8rem;">预估本月积累总额</div>
            <div style="font-size:2.2rem; font-weight:800; color:#16a34a; margin:6px 0;">RM {vault_balance:,.2f}</div>
            <div style="color:#94a3b8; font-size:0.75rem;">包含刚性储蓄 RM {st.session_state.target_savings} 与当前结余</div>
        </div>
        """, unsafe_allow_html=True)
        
    with bank_col2:
        st.markdown("#### 📜 资金变动流水明细")
        bank_statements = [
            {"时间": f"{current_month_str}-01", "事项说明": "月度总收入注入", "金额变动": f"+RM {st.session_state.user_income:,.2f}"},
            {"时间": f"{current_month_str}-01", "事项说明": "固定开支扣除 (房租/水电气)", "金额变动": f"-RM {st.session_state.fixed_expense:,.2f}"},
            {"时间": f"{current_month_str}-01", "事项说明": "划转至强制储蓄金库", "金额变动": f"+RM {st.session_state.target_savings:,.2f}"},
            {"时间": "实时分析", "事项说明": "本月动态消费支出汇总", "金额变动": f"-RM {spent_so_far:,.2f}"}
        ]
        st.dataframe(pd.DataFrame(bank_statements), use_container_width=True, height=220, hide_index=True)

# ----------------- TAB 4: 消费特点测评 -----------------
with tab_quiz:
    questions = [
        {
            "id": 1,
            "title": "当发薪水或收到额外奖金时，您的第一反应通常是？",
            "options": {
                "A": "终于可以买关注很久的东西犒劳自己。",
                "B": "赶紧存起来，看到账户余额增加才安心。",
                "C": "严格按照预先设定的比例划拨到不同账户。"
            }
        },
        {
            "id": 2,
            "title": "在商场或网上看到非刚需但心仪的商品时，您会？",
            "options": {
                "A": "喜欢就买，提升生活品质最重要。",
                "B": "犹豫再三，觉得没必要而放弃。",
                "C": "加入观察清单，评估当月弹性预算后再决定。"
            }
        },
        {
            "id": 3,
            "title": "您对查看账单或记录开销的态度是？",
            "options": {
                "A": "不太想看，感觉钱不知不觉就花了。",
                "B": "经常查看，对每一笔小的开支都比较敏感。",
                "C": "定期复盘开销结构，保持预算在计划内。"
            }
        }
    ]

    if st.session_state.quiz_step == 0:
        st.markdown("## 🧩 消费心理特点测评")
        st.caption("分析您的消费特点 · 匹配个性化省钱建议")
        if st.button("🚀 开始测评", type="primary"):
            st.session_state.quiz_step = 1
            st.session_state.quiz_answers = {}
            st.rerun()

    elif 1 <= st.session_state.quiz_step <= len(questions):
        q = questions[st.session_state.quiz_step - 1]
        st.progress(st.session_state.quiz_step / len(questions), text=f"进度：第 {st.session_state.quiz_step} / {len(questions)} 题")
        
        st.markdown(f"#### Q{q['id']}. {q['title']}")
        selected_opt = st.radio(
            "请选择最符合您的选项：",
            options=list(q["options"].keys()),
            format_func=lambda x: f"**{x}**. {q['options'][x]}",
            key=f"q_{q['id']}"
        )
        
        if st.button("下一题 ➡️", type="primary"):
            st.session_state.quiz_answers[q['id']] = selected_opt
            st.session_state.quiz_step += 1
            st.rerun()

    elif st.session_state.quiz_step > len(questions):
        answers = st.session_state.quiz_answers
        score_A = sum([1 for v in answers.values() if v == "A"])
        score_B = sum([1 for v in answers.values() if v == "B"])
        
        if score_A >= 2:
            personality_res = "冲动享乐型"
            desc = "特点：注重生活品质，弹性消费占比高。管家建议：设冷静期，重点把控娱乐与享乐开销。"
        elif score_B >= 2:
            personality_res = "焦虑防御型"
            desc = "特点：防守意识强，储蓄倾向高。管家建议：适当预留快乐基金，无需对合理消费产生负担。"
        else:
            personality_res = "目标驱动型"
            desc = "特点：理性自律，规划性极强。管家建议：保持节奏，继续向长期财务目标迈进。"

        st.session_state.user_personality = personality_res
        st.success(f"🎉 测评完成！您的消费特点评定为：**{personality_res}**")
        st.info(desc)
        
        if st.button("🔄 重新测试"):
            st.session_state.quiz_step = 0
            st.session_state.quiz_answers = {}
            st.rerun()
