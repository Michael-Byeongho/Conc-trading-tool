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

# --- 3. Main Interface (Tabs) ---
# 데이터 바구니 먼저 생성 (에러 방지)
data = {} 

with st.expander("🌍 시장 가격 및 품위", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        cu_p = st.number_input("Cu Price ($/MT)", value=12000.0)
        cu_a = st.number_input("Cu Assay (%)", value=25.0)
    with c2:
        ag_p = st.number_input("Ag Price ($/Oz)", value=70.0)
        ag_a = st.number_input("Ag Assay (g/t)", value=50.0)
    with c3:
        au_p = st.number_input("Au Price ($/Oz)", value=4500.0)
        au_a = st.number_input("Au Assay (g/t)", value=10.0)

tab1, tab2, tab3 = st.tabs(["📝 조건 입력", "📊 결과 비교", "🎯 협상 가이드"])

cases = [("A (Base)안", "a", 80.0), ("B안", "b", 80.0), ("C안", "c", 80.0)]

with tab1:
    for name, k, def_tc in cases:
        with st.expander(f"📍 {name} 상세 설정", expanded=(k=='a')):
            st.markdown(f"<div class='section-head'>Payable Metals</div>", unsafe_allow_html=True)
            data[f"cu_py_{k}"] = st.number_input(f"Cu Pay (%)", value=100.0, key=f"cp_{k}")
            data[f"cu_dv_{k}"] = st.number_input(f"Cu PD/MD (%)", value=1.0, key=f"cdv_{k}")
            data[f"ag_py_{k}"] = st.number_input(f"Ag Pay (%)", value=90.0, key=f"ap_{k}")
            data[f"ag_dv_{k}"] = st.number_input(f"Ag PD/MD (g/t)", value=30.0, key=f"adv_{k}")
            data[f"au_py_{k}"] = st.number_input(f"Au Pay (%)", value=90.0, key=f"aup_{k}")
            data[f"au_dv_{k}"] = st.number_input(f"Au PD/MD (g/t)", value=1.0, key=f"audv_{k}")
            
            st.markdown(f"<div class='section-head'>Costs (TC/RC)</div>", unsafe_allow_html=True)
            data[f"tc_{k}"] = st.number_input(f"TC ($/t)", value=def_tc, key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input(f"Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
            data[f"ag_rc_{k}"] = st.number_input(f"Ag RC ($/oz)", value=0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input(f"Au RC ($/oz)", value=5.0, key=f"aurc_{k}")
            # 필요한 기본값 채우기
            data[f"cu_dt_{k}"] = "PD"; data[f"ag_dt_{k}"] = "PD"; data[f"au_dt_{k}"] = "PD"

# 계산 수행
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

with tab2:
    st.markdown("### 📈 수익성 비교")
    m1, m2, m3 = st.columns(3)
    m1.metric("A안 (기준)", f"${abs(res['a']):,.2f}")
    m2.metric("B안 이익", f"${abs(res['b']):,.2f}", f"{res['b'] - res['a']:,.2f}")
    m3.metric("C안 이익", f"${abs(res['c']):,.2f}", f"{res['c'] - res['a']:,.2f}")

with tab3:
    st.markdown("### 🎯 Target TC 도출 (A vs B)")
    net_b_no_tc = calc_unit_net(mode, 0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
                                au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
                                ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b'])
    
    if mode == "Purchase (매입)":
        be_tc = res['a'] - net_b_no_tc
        diff_tc = be_tc - data['tc_b']
        is_fav = diff_tc <= 0
    else:
        be_tc = net_b_no_tc - res['a']
        diff_tc = data['tc_b'] - be_tc
        is_fav = diff_tc >= 0

    status_color = "#27ae60" if is_fav else "#e74c3c"
    
    st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);">
            <p style="margin: 0; color: #7f8c8d; font-size: 14px;">🎯 목표 TC (Target TC)</p>
            <p style="margin: 5px 0; color: #2c3e50; font-size: 32px; font-weight: 800;">${be_tc:,.2f}</p>
            <p style="color: {status_color}; font-weight: bold;">{"✅ 현재 조건 유리" if is_fav else "❌ 현재 조건 불리"}</p>
        </div>
        <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 10px; border-left: 5px solid {status_color};">
            A안만큼의 수익을 내려면 <b>TC를 최소 ${be_tc:,.2f}</b> 받아야 합니다.<br>
            현재 B안의 TC(${data['tc_b']:.2f})는 목표보다 <b>${abs(diff_tc):,.2f}</b> {"더 확보된" if is_fav else "부족한"} 상태입니다.
        </div>
    """, unsafe_allow_html=True)

# --- 4. Calculation ---
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

with res_area.container():
    st.markdown("---")
    st.metric("A (비교기준값)", f"${abs(res['a']):,.2f} /t")
    st.metric("B안 이익 (vs A)", f"${abs(res['b']):,.2f} /t", f"{res['b'] - res['a']:,.2f}")
    st.metric("C안 이익 (vs A)", f"${abs(res['c']):,.2f} /t", f"{res['c'] - res['a']:,.2f}")

