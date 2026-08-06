import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import base64

# ==================== 1. 页面基本配置 ====================
st.set_page_config(page_title="PocketSmith AI Ledger", layout="wide", page_icon="💳")

# ==================== 2. 侧边栏：自定义背景图上传与财务设置 ====================
with st.sidebar:
    st.markdown("### 🖼️ 自定义背景图片")
    bg_file = st.file_uploader("上传您喜欢的图片作为背景", type=["jpg", "jpeg", "png", "webp"])
    
    st.markdown("---")
    st.markdown("### ⚙️ 个人财务控制台")
    st.caption("设定您的每月预算基准")

# 转换上传的图片为 CSS 可用的 Base64 编码
bg_css = ""
if bg_file is not None:
    bytes_data = bg_file.read()
    base64_img = base64.b64encode(bytes_data).decode()
    bg_css = f"""
        .stApp {{
            background-image: url("data:image/png;base64,{base64_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{
            background: rgba(255, 255, 255, 0.88);
            padding: 2rem;
            border-radius: 16px;
            margin-top: 1rem;
            backdrop-filter: blur(6px);
        }}
    """
else:
    bg_css = """
        .stApp { background-color: #f8fafc; color: #1e293b; }
    """

st.markdown(f"""
<style>
    {bg_css}
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    
    button[data-testid="stSidebarCollapseButton"],
    button[aria-label="Expand sidebar"],
    button[aria-label="Collapse sidebar"] {{
        visibility: visible !important;
        display: flex !important;
        z-index: 999999 !important;
        opacity: 1 !important;
    }}

    .hero-card {{
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
    }}
    .metric-card {{
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s;
    }}
    .metric-card:hover {{ transform: translateY(-2px); }}
    .metric-label {{ font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; }}
    .metric-value {{ font-size: 1.8rem; font-weight: 800; color: #0f172a; margin-top: 4px; }}
    
    .stButton>button {{
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ==================== 3. 消费人格数据库与权重配置 ====================
PERSONALITY_PROFILES = {
    "脉冲体验者": {
        "desc": "极易被新鲜感与情绪驱动，为即时快乐买单，资金留存率偏低。",
        "advice_rule": "⚠️ 检测到高额/非刚需消费！建议启动 72 小时冷静期，3天后依然想买再决定，可拦截 80% 冲动支出。"
    },
    "沉浸品质家": {
        "desc": "追求质感与深度体验，不在意数量，单笔开销大，现金流易阶段性波动。",
        "advice_rule": "💎 提示：单笔金额较大。请预估使用次数计算“单次使用成本”（CP值），评估是否符合品质基金配额。"
    },
    "策略精算师": {
        "desc": "极致比价，精通规则与满减，享受优惠带来的掌控感，需防范凑单陷阱。",
        "advice_rule": "🧮 提示：请核查是否存在为了满减而凑单非刚需商品的情况，注意计算付出研究的时间成本。"
    },
    "安稳守恒者": {
        "desc": "风险偏好极低，奉行非必要不支出，储蓄安全感极强，资金抗通胀率较低。",
        "advice_rule": "🛡️ 诊断：开销极为克制。刚需消费建议一步到位购买高质量耐用品，避免频繁低价替换带来的长线损耗。"
    },
    "社交随浪者": {
        "desc": "消费易受社交圈、人情及外界评价影响，被动与社交性支出偏高。",
        "advice_rule": "👥 提示：社交/人情类支出请关注“人际社交预算上限”，月末复盘评估该笔社交的实际价值回报。"
    },
    "宏观规划家": {
        "desc": "极度理性自律，每笔开销都服务于长远财务目标与既定预算。",
        "advice_rule": "🎯 诊断：支出符合既定财务规划，未偏离月度控制线，整体资产管理状况稳健。"
    }
}

QUESTIONS_DB = [
    {
        "id": "Q1",
        "title": "连续加班一周后的周末，你最倾向于用哪种方式放松？",
        "options": {
            "A": "狠狠点一顿大餐或买下购物车里搁置很久的衣服",
            "B": "去预约很久的高档SPA、看演出或来一场高品质微度假",
            "C": "找找附近有没有划算的小吃团购或免费的公园展览",
            "D": "宅在家里做饭、追剧、打扫卫生，几乎零支出"
        },
        "weights": {
            "A": {"E":2, "I":2},
            "B": {"Q":2, "S":1},
            "C": {"V":2, "R":1},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q2",
        "title": "在电商大促（如双11、618）期间，你的典型状态是？",
        "options": {
            "A": "看到直播间“最后10秒”就忍不住跟着下单",
            "B": "只买早已看好的大牌耐用品或提升生活质量的大件",
            "C": "提前拉Excel表格计算跨店满减、消费券，务必拿到最低价",
            "D": "基本不关注，手头的东西没坏就不买"
        },
        "weights": {
            "A": {"I":2, "E":2},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "P":2},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q3",
        "title": "朋友突然约你吃一家人均消费超出你平时预算的网红餐厅，你会？",
        "options": {
            "A": "毫不犹豫答应，大家开心最重要，大不了下周省省",
            "B": "欣然前往，如果环境和菜品确实好，觉得很值得",
            "C": "去之前先去各大平台搜一搜有没有优惠券或代金券",
            "D": "找理由婉拒，或者建议换一家性价比更高的地方"
        },
        "weights": {
            "A": {"S":2, "I":2},
            "B": {"Q":2, "S":1},
            "C": {"V":2, "R":1},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q4",
        "title": "购买一件高频使用的电子产品（如手机、电脑）时，你的决策核心是？",
        "options": {
            "A": "外观好看、功能炫酷，有新出的颜色就想买",
            "B": "顶级配置、极佳的使用体验与售后服务，多花点钱也值",
            "C": "挑选很久，必须找到官方补贴、叠加满减后的最低价才下单",
            "D": "性能满足未来3-5年使用即可，绝不超出手头既有预算"
        },
        "weights": {
            "A": {"E":2, "I":1},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "R":1},
            "D": {"P":2, "F":2}
        }
    },
    {
        "id": "Q5",
        "title": "逛街或刷软件时看到一件不在计划内但很喜欢的物件，你会？",
        "options": {
            "A": "瞬间被击中，“不买今天就难受”，直接刷卡",
            "B": "评估它的材质与设计，如果是高品质且能升华居家质感就拿下",
            "C": "拿出手机搜同款，看看有没有更便宜的渠道或二手平台",
            "D": "告诉自己“家里已经有了类似的/不是刚需”，冷静离开"
        },
        "weights": {
            "A": {"I":2, "E":2},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "R":1},
            "D": {"P":2, "F":2}
        }
    },
    {
        "id": "Q6",
        "title": "你对各类会员订阅（如视频VIP、健身卡、音乐软件）的态度是？",
        "options": {
            "A": "看到想看的剧就开一个月，不知不觉扣了许多自动续费",
            "B": "只买高频使用的顶级体验服务（如无广告、高画质、私人教练）",
            "C": "总是等拼单、联合赠送或新用户首月1元优惠时再开",
            "D": "能用免费版的绝不付费，极少开通任何长期订阅"
        },
        "weights": {
            "A": {"I":2, "E":1},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "R":1},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q7",
        "title": "查看上个月的账单时，你的第一反应通常是？",
        "options": {
            "A": "“天呐，我怎么不知不觉花了这么多？钱都去哪了？”",
            "B": "“虽然花了不少，但买到了好东西/体验了棒的项目，值了。”",
            "C": "“虽然支出项多，但算下来靠优惠省下了好几百，很有成就感。”",
            "D": "“基本都在预算控制内，剩余资金可以顺利存入理财账户。”"
        },
        "weights": {
            "A": {"I":2, "E":2},
            "B": {"Q":2, "S":1},
            "C": {"V":2, "R":1},
            "D": {"P":2, "F":2}
        }
    },
    {
        "id": "Q8",
        "title": "关于日常储蓄与理财，你目前的真实习惯是？",
        "options": {
            "A": "随缘攒钱，发了工资先花，月末有剩余才存",
            "B": "攒钱是为了下一次大的品质消费（如旅行、换大件）",
            "C": "喜欢研究各种稳健理财、高息存款，精打细算让钱生钱",
            "D": "严格执行强制储蓄，每月工资一到账就先划走预定比例"
        },
        "weights": {
            "A": {"I":2, "E":1},
            "B": {"Q":2, "S":1},
            "C": {"V":2, "R":2},
            "D": {"P":2, "F":2}
        }
    },
    {
        "id": "Q9",
        "title": "如果你突然获得了一笔计划外的小奖金（如2000元），你会？",
        "options": {
            "A": "奖励自己一场说走就走的旅行或心仪很久的奢品",
            "B": "升级家里的某样生活用品，提升日常生活品质",
            "C": "存起来大半，剩下小部分用来找优惠购买刚需品",
            "D": "100%直接转入储蓄或投资账户，不增加任何额外消费"
        },
        "weights": {
            "A": {"E":2, "I":2},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "F":1},
            "D": {"F":2, "P":2}
        }
    },
    {
        "id": "Q10",
        "title": "面对“买二送一”或“满300减50”这类促销活动，你常做的是？",
        "options": {
            "A": "为了凑满减，不知不觉买了一堆原本没打算买的东西",
            "B": "只有凑单的东西本身符合品质要求时才会顺便凑",
            "C": "精确计算每一件商品的折后单价，甚至找陌生人拼单",
            "D": "保持警惕，坚决不为了凑数而购买不需要的物品"
        },
        "weights": {
            "A": {"I":2, "E":2},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "R":1},
            "D": {"P":2, "F":2}
        }
    },
    {
        "id": "Q11",
        "title": "在处理旧物（如二手衣服、旧家电）时，你一般会？",
        "options": {
            "A": "堆在家里占地方，或者懒得处理直接扔掉",
            "B": "能送人就送人，或者回收给环保机构",
            "C": "细心拍照、撰写文案，挂在二手平台卖掉变现",
            "D": "尽量用到坏为止，极少产生不必要的淘汰旧物"
        },
        "weights": {
            "A": {"I":1, "E":1},
            "B": {"S":1, "Q":1},
            "C": {"V":2, "R":1},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q12",
        "title": "临近月末发现预算有点紧张时，你会怎么应对？",
        "options": {
            "A": "稍微收敛一点，但遇到喜欢的依然会用花呗/信用卡支付",
            "B": "减少不必要的社交活动，但基本的日常饮食品质不下降",
            "C": "开启“极致省钱模式”，顿顿找外卖红包或自己做饭",
            "D": "几乎不会遇到这种情况，因为每月的开销都在严格掌控中"
        },
        "weights": {
            "A": {"I":2, "E":2},
            "B": {"Q":2, "S":1},
            "C": {"V":2, "F":1},
            "D": {"P":2, "F":2}
        }
    },
    {
        "id": "Q13",
        "title": "对于网红打卡地、流行单品或爆款美食，你的态度是？",
        "options": {
            "A": "很感兴趣，愿意排队或付费去尝鲜体验",
            "B": "只有当它确实具备独特的高品质或文化价值时才会去",
            "C": "等热度过了、有优惠券或者打折时再去体验",
            "D": "完全不感冒，对跟风消费天然免疫"
        },
        "weights": {
            "A": {"E":2, "S":1},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "R":1},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q14",
        "title": "你平时对微小支出（如打车代步、外卖配送费、饮料）的感知是？",
        "options": {
            "A": "觉得都是小钱，平时不太在意，累积起来才发现很吓人",
            "B": "只要能节省时间或带来舒适感，花点小钱很值得",
            "C": "极度看重，会尽量用免费骑行券、找免配送费店家",
            "D": "习惯步行/公交，自带水壶，能避免的小开销尽量避免"
        },
        "weights": {
            "A": {"I":2, "E":2},
            "B": {"Q":2, "S":1},
            "C": {"V":2, "R":1},
            "D": {"F":2, "P":1}
        }
    },
    {
        "id": "Q15",
        "title": "你希望这套消费管理系统未来最能帮你解决什么问题？",
        "options": {
            "A": "斩断冲动消费，帮我守住钱包",
            "B": "在不降低生活品质的前提下，优化非必要开支",
            "C": "帮我自动比价和整理优惠，把精打细算做到极致",
            "D": "提供清晰的财务分析图表，辅助我实现长期资产规划"
        },
        "weights": {
            "A": {"E":2, "I":2},
            "B": {"Q":2, "R":1},
            "C": {"V":2, "R":1},
            "D": {"P":2, "F":2}
        }
    }
]

# ==================== 4. Session 状态初始化 ====================
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

# 侧边栏：参数设定
with st.sidebar:
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
    st.markdown("### 🧬 当前消费基因类型")
    st.info(f"**{st.session_state.user_personality}**")

# ==================== 5. 顶部 Header ====================
st.markdown(f"""
<div class="hero-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin:0; font-size: 1.8rem; font-weight: 800;">
                PocketSmith 智能消费管理系统
            </h1>
            <p style="margin: 4px 0 0 0; font-size: 0.9rem; opacity: 0.9;">
                专业理财管家 · 15维消费基因诊断与账单全量存档
            </p>
        </div>
        <div>
            <span style="background: rgba(255, 255, 255, 0.2); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                {'自定义图片背景' if bg_file else '标准背景'}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 指标计算
spent_so_far = st.session_state.ledger_records["金额(RM)"].sum() if not st.session_state.ledger_records.empty else 0.0
remaining_budget = monthly_budget - spent_so_far
daily_safe_spend = max(0.0, round(remaining_budget / 30, 2))

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">月度总收入</div>
        <div class="metric-value" style="color:#0284c7;">RM {st.session_state.user_income:,.2f}</div>
        <div style="font-size:0.8rem; color:#64748b;">固定支出: RM {st.session_state.fixed_expense:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">可自由支配预算</div>
        <div class="metric-value">RM {monthly_budget:,.2f}</div>
        <div style="font-size:0.8rem; color:#64748b;">预留储蓄: RM {st.session_state.target_savings:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">本月累计支出</div>
        <div class="metric-value" style="color:#e11d48;">RM {spent_so_far:,.2f}</div>
        <div style="font-size:0.8rem; color:#64748b;">已存档 {len(st.session_state.ledger_records)} 笔开销</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    rem_color = "#16a34a" if remaining_budget >= 0 else "#dc2626"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">每日安全额度 (Daily Safe)</div>
        <div class="metric-value" style="color:{rem_color};">RM {daily_safe_spend:,.2f}</div>
        <div style="font-size:0.8rem; color:{rem_color};">{'预算控制良好' if remaining_budget>=0 else '超支预警'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== 6. 核心功能 Tab ====================
tab_track, tab_analytics, tab_bank, tab_quiz = st.tabs([
    "✍️ 智能记账与个性化诊断", 
    "📊 消费特点分析图表", 
    "🏦 资金流向与储蓄库", 
    "🧬 消费基因深度测评 (15题)"
])

# ----------------- TAB 1: 记账与专业诊断 -----------------
with tab_track:
    left_col, right_col = st.columns([1.1, 1.9])
    
    with left_col:
        st.markdown("### ➕ 录入开销")
        with st.form("expense_input_form", clear_on_submit=True):
            amount = st.number_input("消费金额 (RM)", min_value=0.0, step=5.0, value=0.0)
            category = st.selectbox("消费分类", ["餐饮美食", "交通出行", "弹性享乐(娱乐/社交)", "日用百货", "数码/大件", "人情/社交", "其他支出"])
            detail = st.text_input("具体明细 / 场景描述", placeholder="例：星巴克咖啡 / 聚餐分摊")
            
            submit_btn = st.form_submit_button("🚀 存档并获取管家诊断", use_container_width=True)
            
            if submit_btn and amount > 0:
                p_name = st.session_state.user_personality.split(" ")[0]
                base_rule = PERSONALITY_PROFILES.get(p_name, {}).get(
                    "advice_rule", 
                    f"🟢 已成功存档！当前每日建议消费上限为 RM {daily_safe_spend}。"
                )
                
                advice = f"【管家诊断 ({p_name})】{base_rule}"
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame([[now_str, current_month_str, amount, category, detail, advice]],
                                       columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家专业建议"])
                
                st.session_state.ledger_records = pd.concat([st.session_state.ledger_records, new_row], ignore_index=True)
                st.success("账单已成功存档并完成基因匹配分析！")
                st.rerun()

    with right_col:
        st.markdown("### 📜 消费历史流水存档 (Transaction Archive)")
        if not st.session_state.ledger_records.empty:
            display_df = st.session_state.ledger_records.iloc[::-1][["日期", "消费分类", "金额(RM)", "具体明细", "理财管家专业建议"]]
            st.dataframe(display_df, use_container_width=True, height=360, hide_index=True)
        else:
            st.info("💡 当前暂无开销存档。在左侧录入第一笔消费即可开启存档与动态诊断！")

# ----------------- TAB 2: 图表分析 -----------------
with tab_analytics:
    if not st.session_state.ledger_records.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### 🍩 消费领域分布占比")
            cat_summary = st.session_state.ledger_records.groupby("消费分类")["金额(RM)"].sum().reset_index()
            fig_pie = px.pie(cat_summary, values="金额(RM)", names="消费分类", hole=0.55)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            st.markdown("#### 📈 消费时间分布与开支流向")
            fig_bar = px.bar(st.session_state.ledger_records, x="日期", y="金额(RM)", color="消费分类")
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("💡 暂无开销数据，请先在第一页录入消费事项。")

# ----------------- TAB 3: 资金与储蓄库 -----------------
with tab_bank:
    st.markdown("### 🏦 资产与预算结余概览")
    vault_balance = st.session_state.target_savings + max(0.0, remaining_budget)
    
    bank_col1, bank_col2 = st.columns([1.1, 1.9])
    with bank_col1:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.85); padding:24px; border-radius:16px; border:1px solid rgba(0,0,0,0.1);">
            <div style="font-size:0.8rem; font-weight:600; color:#64748b;">ESTIMATED TOTAL SAVINGS</div>
            <div style="font-size:0.9rem; margin-top:4px;">预算与储蓄储备账户</div>
            <hr style="margin:15px 0; border-color:#e2e8f0;">
            <div style="font-size:0.8rem; color:#64748b;">预估本月积累总额</div>
            <div style="font-size:2.2rem; font-weight:800; color:#16a34a; margin:6px 0;">RM {vault_balance:,.2f}</div>
            <div style="font-size:0.75rem; color:#64748b;">包含刚性储蓄 RM {st.session_state.target_savings} 与当前结余</div>
        </div>
        """, unsafe_allow_html=True)
        
    with bank_col2:
        st.markdown("#### 📜 资金变动流水明细")
        bank_statements = [
            {"时间": f"{current_month_str}-01", "事项说明": "月度总收入注入", "金额变动": f"+RM {st.session_state.user_income:,.2f}"},
            {"时间": f"{current_month_str}-01", "事项说明": "固定开支扣除 (房租/水电气)", "金额变动": f"-RM {st.session_state.fixed_expense:,.2f}"},
            {"时间": f"{current_month_str}-01", "事項说明": "划转至强制储蓄金库", "金额变动": f"+RM {st.session_state.target_savings:,.2f}"},
            {"时间": "实时动态", "事项说明": "本月累计已录入消费", "金额变动": f"-RM {spent_so_far:,.2f}"}
        ]
        st.dataframe(pd.DataFrame(bank_statements), use_container_width=True, height=220, hide_index=True)

# ----------------- TAB 4: 15题 消费基因深度测评 -----------------
with tab_quiz:
    if st.session_state.quiz_step == 0:
        st.markdown("## 🧬 消费基因深度评估 (全套 15 题)")
        st.caption("基于 8 维特征矩阵 (E/R/Q/V/I/P/S/F)，精准计算你的 6 大消费人格与专属理财战略。")
        if st.button("🚀 开始 15 题深度测评", type="primary"):
            st.session_state.quiz_step = 1
            st.session_state.quiz_answers = {}
            st.rerun()

    elif 1 <= st.session_state.quiz_step <= len(QUESTIONS_DB):
        q = QUESTIONS_DB[st.session_state.quiz_step - 1]
        progress_val = st.session_state.quiz_step / len(QUESTIONS_DB)
        st.progress(progress_val, text=f"评估进度：第 {st.session_state.quiz_step} / {len(QUESTIONS_DB)} 题")
        
        st.markdown(f"#### {q['id']}. {q['title']}")
        
        # 获取上次选择，保持用户交互无缝
        opts = list(q["options"].keys())
        selected_opt = st.radio(
            "请选择最符合你真实生活状态的选项：",
            options=opts,
            format_func=lambda x: f"**{x}**. {q['options'][x]}",
            key=f"q_radio_{q['id']}"
        )
        
        btn_col1, btn_col2 = st.columns([1, 4])
        with btn_col1:
            if st.session_state.quiz_step > 1:
                if st.button("⬅️ 上一题"):
                    st.session_state.quiz_step -= 1
                    st.rerun()
        with btn_col2:
            next_text = "下一题 ➡️" if st.session_state.quiz_step < len(QUESTIONS_DB) else "🏁 完成测评并计算人格"
            if st.button(next_text, type="primary"):
                st.session_state.quiz_answers[q["id"]] = selected_opt
                st.session_state.quiz_step += 1
                st.rerun()

    elif st.session_state.quiz_step > len(QUESTIONS_DB):
        # 计算 8 维总分 (E, R, Q, V, I, P, S, F)
        dim_scores = {"E":0, "R":0, "Q":0, "V":0, "I":0, "P":0, "S":0, "F":0}
        
        for q_item in QUESTIONS_DB:
            qid = q_item["id"]
            user_ans = st.session_state.quiz_answers.get(qid)
            if user_ans and user_ans in q_item["weights"]:
                w_map = q_item["weights"][user_ans]
                for d_k, d_v in w_map.items():
                    dim_scores[d_k] += d_v
        
        # 计算 6 大消费人格得分
        scores = {
            "脉冲体验者": dim_scores["E"] * 1.2 + dim_scores["I"] * 1.2,
            "沉浸品质家": dim_scores["Q"] * 1.5 + dim_scores["R"] * 0.5,
            "策略精算师": dim_scores["V"] * 1.5 + dim_scores["R"] * 0.5,
            "安稳守恒者": dim_scores["F"] * 1.2 + dim_scores["P"] * 1.0,
            "社交随浪者": dim_scores["S"] * 1.5 + dim_scores["E"] * 0.8,
            "宏观规划家": dim_scores["P"] * 1.2 + dim_scores["F"] * 0.8 + dim_scores["R"] * 0.5
        }
        
        # 按得分排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_p, primary_score = sorted_scores[0]
        secondary_p, secondary_score = sorted_scores[1]
        
        # 判断次要人格 (差距小于 15%)
        has_secondary = (primary_score - secondary_score) / (primary_score + 1e-5) < 0.15
        
        final_personality_str = primary_p
        if has_secondary:
            final_personality_str += f" / {secondary_p}"
            
        st.session_state.user_personality = final_personality_str
        
        st.balloons()
        st.success(f"🎉 测评完成！你的专属消费基因定性为：**【{final_personality_str}】**")
        
        p_data = PERSONALITY_PROFILES.get(primary_p, {})
        st.markdown(f"**画像特征**：{p_data.get('desc', '')}")
        st.info(f"**理财管家专属干预逻辑**：\n{p_data.get('advice_rule', '')}")
        
        st.markdown("---")
        st.markdown("#### 📊 你的 6 大人格倾向指数得分")
        score_df = pd.DataFrame(list(scores.items()), columns=["人格类型", "量化得分"]).sort_values(by="量化得分", ascending=False)
        fig_score = px.bar(score_df, x="量化得分", y="人格类型", orientation='h', color="量化得分", color_continuous_scale="Blues")
        fig_score.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
        st.plotly_chart(fig_score, use_container_width=True)
        
        if st.button("🔄 重新测试 15 题"):
            st.session_state.quiz_step = 0
            st.session_state.quiz_answers = {}
            st.rerun()
