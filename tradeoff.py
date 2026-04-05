import streamlit as st
import pandas as pd

# --- 0. Config & Style ---
st.set_page_config(page_title="Trade-off & Sensitivity Tool", layout="wide")
st.markdown("""
<style>
    [data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 8px; border-left: 5px solid #2e4053; }
    .section-head { background-color: #2e4053; color: white; padding: 4px 10px; border-radius: 4px; font-size: 13px; margin: 10px 0; font-weight: bold; }
    .md-hint { font-size: 12px; color: #d35400; font-weight: bold; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# --- 0. Config & Style ---
st.set_page_config(page_title="Trade-off & Sensitivity Tool", layout="wide")

# 무조건 White 모드로 고정하는 CSS
st.markdown("""
    <style>
        /* 기본 배경과 글자색 강제 고정 */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: white !important;
            color: #2c3e50 !important;
        }
        /* 사이드바 배경 고정 */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa !important;
        }
        /* 입력창 라벨 색상 고정 */
        .stMarkdown, p, span, label {
            color: #2c3e50 !important;
        }
        /* 위젯 내부 텍스트 색상 */
        .stNumberInput input, .stSelectbox div {
            color: #2c3e50 !important;
        }
    </style>
""", unsafe_allow_html=True)


# --- 1. Core Logic (PD 가치 계산 시 RC 배제) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, au_p, au_a, au_py, au_rc, au_dt, au_dv, ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    g_to_oz, lb_to_mt = 1/31.1035, 2204.62
    
    # Payable Value (RC 적용)
    v_cu_pay = (cu_a * (cu_py/100) / 100) * (cu_p - (cu_rc/100 * lb_to_mt))
    v_ag_pay = (ag_a * (ag_py/100) * g_to_oz) * (ag_p - ag_rc)
    v_au_pay = (au_a * (au_py/100) * g_to_oz) * (au_p - au_rc)
    
    # PD/MD Value (Market Price 100%)
    d_cu = (cu_dv / 100) * cu_p
    d_ag = (ag_dv * g_to_oz) * ag_p
    d_au = (au_dv * g_to_oz) * au_p
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - (d_cu + d_ag + d_au) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. Sidebar ---
with st.sidebar:
    st.header("💰 실시간 요약")
    mode = st.sidebar.radio("거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)
    res_area = st.empty()

# --- 3. Main Inputs & Tabs ---
# 공통 시장 가격은 상단에 작게 배치 (공간 절약)
with st.expander("🌍 공통 시장 가격 및 품위", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        cu_p = st.number_input("Cu ($/MT)", value=12000.0, step=1.0)
        cu_a = st.number_input("Cu (%)", value=25.0, step=0.01)
    with c2:
        ag_p = st.number_input("Ag ($/Oz)", value=70.0, step=0.01)
        ag_a = st.number_input("Ag (g/t)", value=50.0, step=0.1)
    with c3:
        au_p = st.number_input("Au ($/Oz)", value=4500.0, step=1.0)
        au_a = st.number_input("Au (g/t)", value=10.0, step=0.1)

# 📱 모바일 최적화를 위한 탭 생성
tab1, tab2, tab3 = st.tabs(["📝 조건 입력", "📊 결과 비교", "🎯 협상 가이드"])

with tab1:
    st.markdown("### ⚖️ 안별 조건 설정")
    # 기존 cols = st.columns(3)를 모바일에서는 세로로 보여주되, expander로 감싸서 압축
    cases = [("A (Base)안", "a", 80.0), ("B안", "b", 80.0), ("C안", "c", 80.0)]
    
    for name, k, def_tc in cases:
        with st.expander(f"📍 {name} 상세 설정", expanded=(k=='a')): # A안만 열어두기
            st.write("**[Payables]**")
            data[f"cu_py_{k}"] = st.number_input("Cu Pay (%)", value=100.0, key=f"cp_{k}")
            data[f"cu_dv_{k}"] = st.number_input("Cu PD/MD (%)", value=1.0, key=f"cdv_{k}")
            
            st.write("---")
            data[f"ag_py_{k}"] = st.number_input("Ag Pay (%)", value=90.0, key=f"ap_{k}")
            data[f"ag_dv_{k}"] = st.number_input("Ag PD/MD (g/t)", value=30.0, key=f"adv_{k}")

            st.write("---")
            data[f"au_py_{k}"] = st.number_input("Au Pay (%)", value=90.0, key=f"aup_{k}")
            data[f"au_dv_{k}"] = st.number_input("Au PD/MD (g/t)", value=1.0, key=f"audv_{k}")
            
            st.markdown(f"<div class='section-head'>📉 Costs</div>", unsafe_allow_html=True)
            data[f"tc_{k}"] = st.number_input("TC ($/t)", value=def_tc, key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input("Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
            data[f"ag_rc_{k}"] = st.number_input("Ag RC ($/oz)", value=0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input("Au RC ($/oz)", value=5.0, key=f"aurc_{k}")
            # 불필요한 radio(PD/MD 선택) 등은 생략하거나 data에 기본값 할당 (계산 오류 방지용)
            data[f"cu_dt_{k}"] = "PD"; data[f"ag_dt_{k}"] = "PD"; data[f"au_dt_{k}"] = "PD"

with tab2:
    st.markdown("### 📈 수익성 비교")
    # 계산 로직 실행 (res 딕셔너리 생성 부분)
    res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                            au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                            ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}
    
    # 결과 요약 카드 (세로로 길지 않게 한눈에 표시)
    m1, m2, m3 = st.columns(3)
    m1.metric("A안 (기준)", f"${abs(res['a']):,.2f}")
    m2.metric("B안 이익", f"${abs(res['b']):,.2f}", f"{res['b'] - res['a']:,.2f}")
    m3.metric("C안 이익", f"${abs(res['c']):,.2f}", f"{res['c'] - res['a']:,.2f}")
    
    # 여기에 차트(Plotly) 같은걸 넣으면 폰에서 보기 아주 좋습니다.

with tab3:
    # 🎯 여기에 이전에 만든 [# --- 6. 협상 타겟 계산 ---] 코드를 넣으면 됩니다.
    st.markdown("### 🎯 Target TC 분석")
    # (위에서 만든 Target TC 로직 코드 입력...)





# --- 4. Calculation ---
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

with res_area.container():
    st.markdown("---")
    st.metric("A (비교기준값)", f"${abs(res['a']):,.2f} /t")
    st.metric("B안 이익 (vs A)", f"${abs(res['b']):,.2f} /t", f"{res['b'] - res['a']:,.2f}")
    st.metric("C안 이익 (vs A)", f"${abs(res['c']):,.2f} /t", f"{res['c'] - res['a']:,.2f}")



# --- 6. 협상 타겟 계산 (Break-even TC) ---
st.markdown("---")
st.markdown("### 🎯 협상 가이드: 얼마를 더 받아야하나 (A vs B)")

# 계산 로직 (기존 로직 유지)
net_b_no_tc = calc_unit_net(mode, 0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
                            au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
                            ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b'])

if mode == "Purchase (매입)":
    be_tc = res['a'] - net_b_no_tc
    diff_tc = be_tc - data['tc_b']
    is_favorable = diff_tc <= 0
else:
    be_tc = net_b_no_tc - res['a']
    diff_tc = data['tc_b'] - be_tc
    is_favorable = diff_tc >= 0

# --- 커스텀 스타일 적용 ---
status_color = "#27ae60" if is_favorable else "#e74c3c"
status_text = "유리 (Favorable)" if is_favorable else "불리 (Unfavorable)"
bg_color = "#f8fff9" if is_favorable else "#fff8f8"
border_color = "#2ecc71" if is_favorable else "#ff7675"

c_be1, c_be2 = st.columns([1, 2])

with c_be1:
    # 목표 TC 카드 디자인
    st.markdown(f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); text-align: center;">
            <p style="margin: 0; color: #7f8c8d; font-size: 14px; font-weight: 600;">🎯 목표 TC (Target TC)</p>
            <p style="margin: 5px 0; color: #2c3e50; font-size: 32px; font-weight: 800;">${be_tc:,.2f}</p>
            <div style="height: 4px; background-color: {status_color}; width: 60%; margin: 10px auto; border-radius: 2px;"></div>
            <p style="margin: 0; color: {status_color}; font-size: 13px; font-weight: bold;">{status_text}</p>
        </div>
    """, unsafe_allow_html=True)

with c_be2:
    # 가이드 문구 및 상세 분석
    st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; border-left: 5px solid {border_color}; min-height: 140px;">
            <p style="margin: 0 0 10px 0; color: #2c3e50; font-size: 15px; font-weight: bold;">📊 B안 협상 가이드</p>
            <p style="margin: 0; color: #34495e; font-size: 14px; line-height: 1.6;">
                상대방의 <b>Payable/RC 조건</b>을 수용한다면, 기존 수익(A안)을 지키기 위해 
                당신은 <b>TC를 최소 ${be_tc:,.2f} 이상</b> 확보해야 합니다.
            </p>
            <div style="margin-top: 15px; font-size: 14px;">
                {f"❌ <b>현재 제안(${data['tc_b']:.2f})</b>은 목표보다 <b><span style='color:{status_color}'>${abs(diff_tc):,.2f}</span></b> 부족합니다." if not is_favorable else 
                 f"✅ <b>현재 제안(${data['tc_b']:.2f})</b>은 목표보다 <b><span style='color:{status_color}'>${abs(diff_tc):,.2f}</span></b> 더 받아낸 상태입니다."}
            </div>
        </div>
    """, unsafe_allow_html=True)
