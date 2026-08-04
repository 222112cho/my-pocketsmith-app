import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# ==================== 1. 页面配置与 PocketSmith 极客暗黑 UI (CSS) ====================
st.set_page_config(page_title="PocketSmith AI Ledger", layout="wide", page_icon="💳")

st.markdown("""
<style>
    /* 全局背景：极客深色系 */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 顶部 Banner 霓虹渐变卡片 */
    .hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        padding: 22px 28px;
        border-radius: 16px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 20px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
    }
    
    /* 高级 Metric 仪表盘卡片 */
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-subtext {
        font-size: 0.78rem;
        margin-top: 4px;
    }

    /* 表格样式定制 */
    div[data-testid="stDataFrame"] {
        background-color: #111827 !important;
        border-radius: 12px !important;
        border: 1px solid #1f2937 !important;
        padding: 8px;
    }
    
    /* 按钮与输入框定制 */
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4f46e5 0%, #4338ca 100%);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5);
    }

    /* Tab 选项卡样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #111827;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #1f2937;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #9ca3af;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f2937 !important;
        color: #818cf8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 2. Session 独立会话状态初始化（全新登录感） ====================
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

# 内存级临时账本数据 (单次会话隔离，保持全新体验)
if "ledger_records" not in st.session_state:
    st.session_state.ledger_records = pd.DataFrame(
        columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家建议"]
    )

# 计算财务沙盘数据
monthly_budget = st.session_state.user_income - st.session_state.fixed_expense - st.session_state.target_savings
current_month_str = datetime.now().strftime("%Y-%m")

# ==================== 3. 侧边栏：自定义个人财务看板 ====================
with st.sidebar:
    st.markdown("### ⚙️ 个人财务沙盘设置")
    st.caption("自定义你的每月收支目标 (全动态计算)")
    
    st.session_state.user_income = st.number_input(
        "💵 每月总收入 (RM)", min_value=0.0, step=100.0, value=st.session_state.user_income
    )
    st.session_state.fixed_expense = st.number_input(
        "🏠 固定刚性支出 (房租/水电气/网费) (RM)", min_value=0.0, step=50.0, value=st.session_state.fixed_expense
    )
    st.session_state.target_savings = st.number_input(
        "🎯 预计强制储蓄目标 (RM)", min_value=0.0, step=50.0, value=st.session_state.target_savings
    )
    
    st.markdown("---")
    st.markdown("### 🧬 你的财商心理画像")
    st.info(f"**{st.session_state.user_personality}**")
    st.caption("💡 可前往【PocketSmith 财商心理测评】Tab 重新测试。")

# ==================== 4. 顶部 Header ====================
st.markdown(f"""
<div class="hero-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="color: white; margin:0; font-size: 1.8rem; font-weight: 800; letter-spacing: 0.5px;">
                PocketSmith AI Ledger
            </h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 0.9rem;">
                智能消费管理系统
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                当前模式: 独享独立会话
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 计算消费数据
spent_so_far = st.session_state.ledger_records["金额(RM)"].sum() if not st.session_state.ledger_records.empty else 0.0
remaining_budget = monthly_budget - spent_so_far
daily_safe_spend = max(0.0, round(remaining_budget / 30, 2))

# 4大卡片仪表盘
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">月度总收入</div>
        <div class="metric-value" style="color:#38bdf8;">RM {st.session_state.user_income:,.2f}</div>
        <div class="metric-subtext" style="color:#94a3b8;">固定支出: RM {st.session_state.fixed_expense:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">可自由支配预算</div>
        <div class="metric-value">RM {monthly_budget:,.2f}</div>
        <div class="metric-subtext" style="color:#94a3b8;">已预留储蓄: RM {st.session_state.target_savings:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    spent_color = "#ef4444" if spent_so_far > monthly_budget else "#f59e0b"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">本月已累计消费</div>
        <div class="metric-value" style="color:{spent_color};">RM {spent_so_far:,.2f}</div>
        <div class="metric-subtext" style="color:#94a3b8;">已记录 {len(st.session_state.ledger_records)} 笔开销</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    rem_color = "#10b981" if remaining_budget >= 0 else "#ef4444"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">每日建议上限 (Daily Safe)</div>
        <div class="metric-value" style="color:{rem_color};">RM {daily_safe_spend:,.2f}</div>
        <div class="metric-subtext" style="color:{rem_color};">{'预算健康' if remaining_budget>=0 else '额度超支预警'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== 5. 核心 Tab 功能区 ====================
tab_track, tab_analytics, tab_bank, tab_quiz = st.tabs([
    "✍️ 极速记账与 AI 管家", 
    "📊 PocketSmith 消费分析", 
    "🏦 模拟银行", 
    "🧩 财商心理测评"
])

# ----------------- TAB 1: 记账与 AI 分析 -----------------
with tab_track:
    left_col, right_col = st.columns([1.1, 1.9])
    
    with left_col:
        st.markdown("### ➕ 记录新开销")
        with st.form("expense_input_form", clear_on_submit=True):
            amount = st.number_input("消费金额 (RM)", min_value=0.0, step=5.0, value=0.0)
            category = st.selectbox("消费领域分类", ["餐饮美食", "交通出行", "弹性享乐(娱乐/社交)", "日用百货", "数码/大件", "其他支出"])
            detail = st.text_input("具体明细 / 场景描述", placeholder="例：Starbucks 咖啡 / 朋友聚餐")
            
            submit_btn = st.form_submit_button("🚀 提交并获取 AI 管家诊断", use_container_width=True)
            
            if submit_btn and amount > 0:
                # 性格化的专业 AI 建议分析
                personality = st.session_state.user_personality
                if "冲动享乐" in personality:
                    if category in ["弹性享乐(娱乐/社交)", "餐饮美食"] and amount > 50:
                        advice = f"🚨 【冲动预警】：检测到开支 RM {amount}！建议开启 10 分钟冷静期，避免连续犒赏性开支。"
                    else:
                        advice = f"🟢 记录成功。请控制每日支出在 RM {daily_safe_spend} 以内。"
                elif "焦虑防御" in personality:
                    if category in ["弹性享乐(娱乐/社交)", "餐饮美食"]:
                        advice = f"🟢 【适度犒赏】：支出 RM {amount} 在合理范围内，适度享受生活是可持续理财的一部分！"
                    else:
                        advice = f"🟢 消费符合防线规划，金库状态极佳。"
                elif "目标驱动" in personality:
                    advice = f"🎯 【目标评估】：已记账 RM {amount}。本月尚余 RM {max(0.0, remaining_budget - amount):,.2f} 可自由支配。"
                else:
                    advice = "🟢 记录成功！消费在预算控制范围内。" if remaining_budget >= amount else "⚠️ 警告：当前消费已超出每日预算预警线。"
                
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame([[now_str, current_month_str, amount, category, detail, advice]],
                                       columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家建议"])
                
                st.session_state.ledger_records = pd.concat([st.session_state.ledger_records, new_row], ignore_index=True)
                st.success("账目已实时记入数据库！")
                st.rerun()

    with right_col:
        st.markdown("### 📜 交易流水账单 (Live Ledger)")
        if not st.session_state.ledger_records.empty:
            display_df = st.session_state.ledger_records.iloc[::-1][["日期", "消费分类", "金额(RM)", "具体明细", "理财管家建议"]]
            st.dataframe(display_df, use_container_width=True, height=360, hide_index=True)
        else:
            st.info("💡 页面已初始化，当前无交易记录。请在左侧录入你的第一笔开销！")

# ----------------- TAB 2: 图表分析 -----------------
with tab_analytics:
    if not st.session_state.ledger_records.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### 🍩 消费占比 (Expense Breakdown)")
            cat_summary = st.session_state.ledger_records.groupby("消费分类")["金额(RM)"].sum().reset_index()
            fig_pie = px.pie(cat_summary, values="金额(RM)", names="消费分类", hole=0.6,
                             color_discrete_sequence=px.colors.qualitative.Dark24)
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'), margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            st.markdown("#### 📈 动态开支流向 (Spending Stream)")
            fig_bar = px.bar(st.session_state.ledger_records, x="日期", y="金额(RM)", color="消费分类",
                             color_discrete_sequence=px.colors.qualitative.Bold)
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'), xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#1e293b'), margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("💡 暂无分析数据，记账后即可解锁 PocketSmith 深度视图。")

# ----------------- TAB 3: 模拟银行 -----------------
with tab_bank:
    st.markdown("### 🏦 DIGITAL VAULT (银行户口)")
    
    vault_balance = st.session_state.target_savings + max(0.0, remaining_budget)
    
    bank_col1, bank_col2 = st.columns([1.1, 1.9])
    with bank_col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #111827 0%, #1f2937 100%); padding:24px; border-radius:16px; border:1px solid #374151;">
            <div style="color:#94a3b8; font-size:0.8rem; font-weight:600;">SAVINGS & RESERVE ACCOUNT</div>
            <div style="color:#6366f1; font-size:0.9rem; margin-top:4px;">9527-****-****-8888</div>
            <hr style="border-color:#374151; margin:15px 0;">
            <div style="color:#94a3b8; font-size:0.8rem;">估计预估总资产 (Available Balance)</div>
            <div style="font-size:2.2rem; font-weight:800; color:#10b981; margin:6px 0;">RM {vault_balance:,.2f}</div>
            <div style="color:#64748b; font-size:0.75rem;">包含本月强制储蓄 RM {st.session_state.target_savings} 与预算剩余</div>
        </div>
        """, unsafe_allow_html=True)
        
    with bank_col2:
        st.markdown("#### 📜 银行模拟流水账单")
        bank_statements = [
            {"交易时间": f"{current_month_str}-01 09:00", "摘要": "月度预算与收入注入", "变动金额": f"+RM {st.session_state.user_income:,.2f}", "状态": "成功"},
            {"交易时间": f"{current_month_str}-01 09:05", "摘要": "固定支出扣除 (房租/水电气)", "变动金额": f"-RM {st.session_state.fixed_expense:,.2f}", "状态": "成功"},
            {"交易时间": f"{current_month_str}-01 09:10", "摘要": "强制储蓄划转至 Vault 账户", "变动金额": f"+RM {st.session_state.target_savings:,.2f}", "状态": "成功"},
            {"交易时间": "实时运行中", "摘要": "本月累计动态消费扣减", "变动金额": f"-RM {spent_so_far:,.2f}", "状态": "同步中"}
        ]
        st.dataframe(pd.DataFrame(bank_statements), use_container_width=True, height=220, hide_index=True)

# ----------------- TAB 4: PocketSmith 财商心理测评 -----------------
with tab_quiz:
    questions = [
        {
            "id": 1,
            "title": "当发薪水或收到一笔额外奖金时，你的第一反应是？",
            "options": {
                "A": "终于可以去买那个关注很久的好东西犒劳自己了！",
                "B": "赶紧存起来或拿去还账，看到账户数字变多才安心。",
                "C": "严格按照预先设定的比例分配：储蓄、投资与生活费。"
            }
        },
        {
            "id": 2,
            "title": "在商场或网上看到一件很喜欢但并非刚需的商品，你会？",
            "options": {
                "A": "喜欢就买！人生苦短，及时行乐最重要。",
                "B": "纠结半天，最后觉得太贵/没必要，满怀罪恶感地放弃。",
                "C": "先加入购物车观察几天，评估当月预算后再做决定。"
            }
        },
        {
            "id": 3,
            "title": "你对定期查看银行卡余额或记账的态度是？",
            "options": {
                "A": "不太敢看，感觉钱不知不觉就花光了。",
                "B": "每天看好几次，花了一两块钱都会焦虑很久。",
                "C": "定期复盘，对自己的现金流心中有数，不慌不忙。"
            }
        },
        {
            "id": 4,
            "title": "你理财的终极核心动机是什么？",
            "options": {
                "A": "提高当下的生活品质，享受眼前的美好。",
                "B": "应对未知的风险与不确定性，安全感第一。",
                "C": "实现具体的财务自由目标或买房买车计划。"
            }
        }
    ]

    if st.session_state.quiz_step == 0:
        st.markdown("## 🧩 财商消费心理测评")
        st.caption("探索你的潜意识消费模式 · 开启定制化 AI 省钱诊断")
        
        st.markdown("💡 理财不只是冷冰冰的计算，更是**消费心理学**。测试将帮你识别消费习惯，并自动匹配 AI 决策建议！")
        if st.button("🚀 开始测评 (预计耗时 1 分钟)", type="primary"):
            st.session_state.quiz_step = 1
            st.session_state.quiz_answers = {}
            st.rerun()

    elif 1 <= st.session_state.quiz_step <= len(questions):
        q = questions[st.session_state.quiz_step - 1]
        st.progress(st.session_state.quiz_step / len(questions), text=f"进度：第 {st.session_state.quiz_step} / {len(questions)} 题")
        
        st.markdown(f"#### Q{q['id']}. {q['title']}")
        selected_opt = st.radio(
            "请选择最符合你直觉的选项：",
            options=list(q["options"].keys()),
            format_func=lambda x: f"**{x}**. {q['options'][x]}",
            key=f"q_{q['id']}"
        )
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.session_state.quiz_step > 1:
                if st.button("⬅️ 上一题"):
                    st.session_state.quiz_step -= 1
                    st.rerun()
        with btn_col2:
            btn_text = "下一题 ➡️" if st.session_state.quiz_step < len(questions) else "🏁 提交并生成心理画像"
            if st.button(btn_text, type="primary"):
                st.session_state.quiz_answers[q['id']] = selected_opt
                st.session_state.quiz_step += 1
                st.rerun()

    elif st.session_state.quiz_step > len(questions):
        answers = st.session_state.quiz_answers
        score_A = sum([1 for v in answers.values() if v == "A"])
        score_B = sum([1 for v in answers.values() if v == "B"])
        
        if score_A >= 2:
            personality_res = "冲动享乐型 (Hedonist)"
            desc = "你重视当下生活体验！大方且懂得享受，但容易产生情绪化消费。管家建议：设立强制冷静期。"
        elif score_B >= 2:
            personality_res = "焦虑防御型 (Guardian)"
            desc = "你有极强的避险意识！但有时过度绷紧，犒赏自己会有罪恶感。管家建议：设立适度消费‘快乐基金’。"
        else:
            personality_res = "目标驱动型 (Architect)"
            desc = "理性架构师！规划性极强，不易跟风。管家建议：保持节奏，注重长远资产配置。"

        st.session_state.user_personality = personality_res
        
        st.balloons()
        st.success(f"🎉 测评完成！你的财商心理画像已更新为：**{personality_res}**")
        st.info(desc)
        
        if st.button("🔄 重新测试"):
            st.session_state.quiz_step = 0
            st.session_state.quiz_answers = {}
            st.rerun()