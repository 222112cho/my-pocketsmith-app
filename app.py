import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import base64

# ==================== 1. 页面基本配置 ====================
st.set_page_config(page_title="智能消费管理系统", layout="wide", page_icon="salary.png")

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
        "desc": "极易被新鲜感与情绪驱动，进行冲动消费，资金留存率偏低。",
        "advice_rule": "拦截建议：消费前思考是否真实存在这项需求后再决定，降低冲动支出的概率。"
    },
    "沉浸品质家": {
        "desc": "追求质感与深度体验，不在意数量，单笔开销大，现金流易阶段性波动。",
        "advice_rule": "诊断提示：请评估预估使用次数并计算单次使用成本，评估是否符合品质基金配额。"
    },
    "策略精算师": {
        "desc": "精通规则与凑单，享受优惠带来的掌控感，需防范凑单陷阱。",
        "advice_rule": "诊断提示：核查是否存在为了凑满减而购买非刚需商品的情况，注意计算付出研究的时间成本。"
    },
    "安稳守恒者": {
        "desc": "风险偏好极低，奉行非必要不支出，储蓄安全感极强，资金抗通胀率较低。",
        "advice_rule": "诊断提示：开销极为克制。刚需消费建议一步到位购买高质量耐用品，降低长期维护损耗。"
    },
    "社交随浪者": {
        "desc": "消费易受社交圈、人情及外界评价影响，被动与社交性支出偏高。",
        "advice_rule": "诊断提示：请关注人际社交预算上限，月末复盘评估该笔社交的实际投资回报率（ROI）。"
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
            "A": "狠狠点一顿大餐或买下购物车里搁置很久的衣服",
            "B": "去预约很久的高档 SPA、看演出或来一场高品质微度假",
            "C": "找找附近有没有划算的小吃团购或免费的公园展览",
            "D": "宅在家里做饭、追剧、打扫卫生，几乎零支出"
        },
        "weights": {"A": {"E":2, "I":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q2",
        "title": "在电商大促（如双 11、618）期间，你的典型状态是？",
        "options": {
            "A": "看到直播间“最后 10 秒”就忍不住跟着下单",
            "B": "只买早已看好的大牌耐用品或提升生活质量的大件",
            "C": "提前拉 Excel 表格计算跨店满减、消费券，务必拿到最低价",
            "D": "基本不关注，手头的东西没坏就不买"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "P":2}, "D": {"F":2, "P":1}}
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
        "weights": {"A": {"S":2, "I":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q4",
        "title": "购买一件高频使用的电子产品（如手机、电脑）时，你的决策核心是？",
        "options": {
            "A": "外观好看、功能炫酷，有新出的颜色就想买",
            "B": "顶级配置、极佳的使用体验与售后服务，多花点钱也值",
            "C": "挑选很久，必须找到官方补贴、叠加满减后的最低价才下单",
            "D": "性能满足未来 3-5 年使用即可，绝不超出手头既有预算"
        },
        "weights": {"A": {"E":2, "I":1}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
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
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q6",
        "title": "你对各类会员订阅（如视频 VIP、健身卡、音乐软件）的态度是？",
        "options": {
            "A": "看到想看的剧就开一个月，不知不觉扣了许多自动续费",
            "B": "只买高频使用的顶级体验服务（如无广告、高画质、私人教练）",
            "C": "总是等拼单、联合赠送或新用户首月 1 元优惠时再开",
            "D": "能用免费版的绝不付费，极少开通任何长期订阅"
        },
        "weights": {"A": {"I":2, "E":1}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
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
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
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
        "weights": {"A": {"I":2, "E":1}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":2}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q9",
        "title": "如果你突然获得了一笔计划外的小奖金（如 2000 元），你会？",
        "options": {
            "A": "奖励自己一场说走就走的旅行或心仪很久的奢品",
            "B": "升级家里的某样生活用品，提升日常生活品质",
            "C": "存起来大半，剩下小部分用来找优惠购买刚需品",
            "D": "100% 直接转入储蓄或投资账户，不增加任何额外消费"
        },
        "weights": {"A": {"E":2, "I":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "F":1}, "D": {"F":2, "P":2}}
    },
    {
        "id": "Q10",
        "title": "面对“买二送一”或“满 300 减 50”这类促销活动，你常做的是？",
        "options": {
            "A": "为了凑满减，不知不觉买了一堆原本没打算买的东西",
            "B": "只有凑单的东西本身符合品质要求时才会顺便凑",
            "C": "精确计算每一件商品的折后单价，甚至找陌生人拼单",
            "D": "保持警惕，坚决不为了凑数而购买不需要的物品"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
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
        "weights": {"A": {"I":1, "E":1}, "B": {"S":1, "Q":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q12",
        "title": "临近月末发现预算有点紧张时，你会怎么应对？",
        "options": {
            "A": "稍微收敛一点，但遇到喜欢的依然会用信用卡/信用支付",
            "B": "减少不必要的社交活动，但基本的日常饮食品质不下降",
            "C": "开启“极致省钱模式”，顿顿找外卖红包或自己做饭",
            "D": "几乎不会遇到这种情况，因为每月的开销都在严格掌控中"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "F":1}, "D": {"P":2, "F":2}}
    },
    {
        "id": "Q13",
        "title": "对于网红打卡地、流行单品或爆款美食，你的态度是？",
        "options": {
            "A": "很感兴趣，愿意排队或付费去尝鲜体验",
            "B": "只有当它确实具备独特的高品质或文化价值时才会去",
            "C": "等热度过了、有优惠券或者打折时再去体验",
            "D": "完全不感兴趣，对跟风消费天然免疫"
        },
        "weights": {"A": {"E":2, "S":1}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
    },
    {
        "id": "Q14",
        "title": "你平时对微小支出（如打车代步、外卖配送费、饮料）的感知是？",
        "options": {
            "A": "觉得都是小钱，平时不太在意，累积起来才发现很大",
            "B": "只要能节省时间或带来舒适感，花点小钱很值得",
            "C": "极度看重，会尽量用免费骑行券、找免配送费店家",
            "D": "习惯步行/公交，自带水壶，能避免的小开销尽量避免"
        },
        "weights": {"A": {"I":2, "E":2}, "B": {"Q":2, "S":1}, "C": {"V":2, "R":1}, "D": {"F":2, "P":1}}
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
        "weights": {"A": {"E":2, "I":2}, "B": {"Q":2, "R":1}, "C": {"V":2, "R":1}, "D": {"P":2, "F":2}}
    }
]

# ==================== 4. 全局通用样式设置 (统一背景与浅色按钮) ====================
with st.sidebar:
    st.markdown("### 自定义背景图片")
    bg_file = st.file_uploader("上传背景图片", type=["jpg", "jpeg", "png", "webp"])
    st.markdown("---")
    st.markdown("### 个人财务控制台")
    st.session_state.user_income = st.number_input("每月总收入 (RM)", min_value=0.0, step=100.0, value=st.session_state.user_income)
    st.session_state.fixed_expense = st.number_input("刚性固定支出 (RM)", min_value=0.0, step=50.0, value=st.session_state.fixed_expense)
    st.session_state.target_savings = st.number_input("强制储蓄目标 (RM)", min_value=0.0, step=50.0, value=st.session_state.target_savings)

bg_css = ""
if bg_file is not None:
    bytes_data = bg_file.read()
    base64_img = base64.b64encode(bytes_data).decode()
    bg_css = f"""
        .stApp {{
            background-image: url("data:image/png;base64,{base64_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
    """
else:
    bg_css = ".stApp { background-color: #f8fafc; color: #0f172a; }"

st.markdown(f"""
<style>
    {bg_css}
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}

    /* 全局按钮浅色调重置 (包括 Primary 与 Default 按钮) */
    div.stButton > button, div.stButton > button[kind="primary"] {{
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button:hover, div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
        border-color: #94a3b8 !important;
        color: #0284c7 !important;
    }}

    /* 顶部卡片 */
    .hero-card {{
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: #ffffff;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    
    /* 概览指标卡片 */
    .metric-card {{
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .metric-label {{ font-size: 0.85rem; color: #64748b; font-weight: 600; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 4px; }}

    /* 鲜明亮丽的管家 Instruction 提示框 */
    .instruction-box {{
        background-color: #fef08a;
        border-left: 6px solid #eab308;
        color: #713f12;
        padding: 16px 20px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 1.05rem;
        margin-top: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}

    /* Quiz 选项卡片与浅色微光样式 */
    .quiz-question-box {{
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
    }}
    
    div[role="radiogroup"] label {{
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 12px 18px !important;
        margin-bottom: 8px !important;
        transition: all 0.2s ease !important;
    }}
    div[role="radiogroup"] label:hover {{
        border-color: #0284c7 !important;
        background: #f0f9ff !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==================== 5. 路由逻辑切换 ====================

# ----------------- 场景 A: 测评页面 (背景统一，按钮浅色，不默认选中) -----------------
if st.session_state.in_quiz_mode:
    st.title("消费基因深度评估")
    st.caption("基于 8 维特征计分法构建，完成 15 道心理测验后，系统将生成您的专属性格与管家诊断逻辑。")
    
    total_q = len(QUESTIONS_DB)
    curr_step = st.session_state.quiz_step
    
    if curr_step <= total_q:
        q_data = QUESTIONS_DB[curr_step - 1]
        
        progress_val = curr_step / total_q
        st.progress(progress_val, text=f"评估进度：第 {curr_step} / {total_q} 题")
        
        st.markdown(f"""
        <div class="quiz-question-box">
            <h4 style="color: #0f172a; margin:0;">{q_data['id']}. {q_data['title']}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        opts = list(q_data["options"].keys())
        
        # index=None 保证取消默认选中，必须由用户自主点击
        selected_opt = st.radio(
            "请选择最契合您真实心理的选项：",
            options=opts,
            index=None,
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
                if st.button("中途退出", use_container_width=True):
                    st.session_state.in_quiz_mode = False
                    st.rerun()
                    
        with b_col3:
            btn_label = "下一题" if curr_step < total_q else "生成我的基因报告"
            if st.button(btn_label, type="primary", use_container_width=True):
                if selected_opt is None:
                    st.warning("请先点击选择一个选项后再继续！")
                else:
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
        
        st.success(f"评估完成！您的专属消费人格定性为：【{final_personality_str}】")
        
        p_info = PERSONALITY_PROFILES.get(primary_p, {})
        st.markdown(f"**【画像特征】**：{p_info.get('desc')}")
        
        # 鲜艳样式的 Instruction
        st.markdown(f"""
        <div class="instruction-box">
            管家诊断指导原则：<br>{p_info.get('advice_rule')}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 6 大消费维度分布图")
        score_df = pd.DataFrame(list(scores.items()), columns=["人格类型", "得分"]).sort_values(by="得分", ascending=True)
        fig_score = px.bar(score_df, x="得分", y="人格类型", orientation='h', color="得分", color_continuous_scale="Blues")
        fig_score.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_score, use_container_width=True)
        
        if st.button("保存结果并返回主管理系统", type="primary", use_container_width=True):
            st.session_state.in_quiz_mode = False
            st.rerun()

# ----------------- 场景 B: 主记账管理页面 -----------------
else:
    monthly_budget = st.session_state.user_income - st.session_state.fixed_expense - st.session_state.target_savings
    spent_so_far = st.session_state.ledger_records["金额(RM)"].sum() if not st.session_state.ledger_records.empty else 0.0
    remaining_budget = monthly_budget - spent_so_far
    daily_safe_spend = max(0.0, round(remaining_budget / 30, 2))
    current_month_str = datetime.now().strftime("%Y-%m")

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(f"""
        <div class="hero-card">
            <h2 style="margin:0; font-size:1.6rem;">理财管家 - 智能消费管理系统</h2>
            <p style="margin:6px 0 0 0; opacity:0.85; font-size:0.95rem;">
                当前已匹配模型：【{st.session_state.user_personality}】
            </p>
        </div>
        """, unsafe_allow_html=True)
    with head_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("进入消费基因测评", type="primary", use_container_width=True):
            st.session_state.in_quiz_mode = True
            st.session_state.quiz_step = 1
            st.session_state.quiz_answers = {}
            st.rerun()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">每月总收入</div><div class="metric-value">RM {st.session_state.user_income:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">自由支配预算</div><div class="metric-value">RM {monthly_budget:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">已累计支出</div><div class="metric-value" style="color:#b91c1c;">RM {spent_so_far:,.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">每日安全额度</div><div class="metric-value" style="color:#15803d;">RM {daily_safe_spend:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["智能记账与即时诊断", "消费特点分析图表", "资金流向与储蓄库"])

    with tab1:
        l_col, r_col = st.columns([1.1, 1.9])
        with l_col:
            st.markdown("### 录入单笔开销")
            with st.form("input_form", clear_on_submit=True):
                amount = st.number_input("消费金额 (RM)", min_value=0.0, step=5.0)
                category = st.selectbox("消费分类", ["餐饮美食", "交通出行", "弹性享乐(娱乐/社交)", "日用百货", "数码/大件", "人情/社交", "其他支出"])
                detail = st.text_input("具体明细描述", placeholder="例如：咖啡 / 餐厅用餐 / 数码配件")
                
                submitted = st.form_submit_button("提交并生成管家建议", use_container_width=True)
                if submitted:
                    if amount > 0:
                        primary_p = st.session_state.user_personality.split(" ")[0]
                        rule = PERSONALITY_PROFILES.get(primary_p, {}).get("advice_rule", f"账单已记录。建议将每日开销控制在 RM {daily_safe_spend} 以内。")

                        advice = f"{rule}"
                        local_now = datetime.utcnow() + timedelta(hours=8)
                        now_str = local_now.strftime("%Y-%m-%d %H:%M:%S")
                        
                        new_data = pd.DataFrame([[now_str, current_month_str, amount, category, detail, advice]],
                                                columns=["日期", "所属月份", "金额(RM)", "消费分类", "具体明细", "理财管家专业建议"])
                        st.session_state.ledger_records = pd.concat([st.session_state.ledger_records, new_data], ignore_index=True)
                        st.success("账单提交成功！已生成对应省钱建议并完成存档。")
                        st.rerun()

        with r_col:
            st.markdown("### 账单历史存档")
            if not st.session_state.ledger_records.empty:
                st.dataframe(st.session_state.ledger_records.iloc[::-1][["日期", "消费分类", "金额(RM)", "具体明细", "理财管家专业建议"]], use_container_width=True, height=380, hide_index=True)
            else:
                st.info("暂无开销记录。请在左侧表单输入您的第一笔开销。")

    with tab2:
        if not st.session_state.ledger_records.empty:
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 消费分类占比")
                pie_df = st.session_state.ledger_records.groupby("消费分类")["金额(RM)"].sum().reset_index()
                st.plotly_chart(px.pie(pie_df, values="金额(RM)", names="消费分类", hole=0.4), use_container_width=True)
            with g2:
                st.markdown("#### 消费趋势")
                st.plotly_chart(px.bar(st.session_state.ledger_records, x="日期", y="金额(RM)", color="消费分类"), use_container_width=True)
        else:
            st.info("暂无数据可供分析。")

    with tab3:
        st.markdown("### 资产与预估积累")
        st.metric("预估本月积累总额 (含强制储蓄)", f"RM {st.session_state.target_savings + max(0.0, remaining_budget):,.2f}")
