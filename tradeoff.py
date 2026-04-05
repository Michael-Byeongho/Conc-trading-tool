import streamlit as st
import pandas as pd

# --- 0. Config & Style ---
st.set_page_config(page_title="Trade-off Tool", layout="wide")
st.markdown("""
    <style>
        :root { --primary-color: #2e4053; }
        [data-testid="stAppViewContainer"] { background-color: white !important; color: #2c3e50 !important; }
        [data-testid="stHeader"] { background-color: white !important; }
        [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
        .section-head { background-color: #2e4053; color: white; padding: 5px 10px; border-radius: 5px; font-size: 14px; margin-top: 15px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, au_p, au_a, au_py, au_rc, au_dt, au_dv, ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    g_to_oz, lb_to_mt = 1/31.1035, 2204.62
    v_cu_pay = (cu_a * (cu_py/100) / 100) * (cu_p - (cu_rc/100 * lb_to_mt))
    v_ag_pay = (ag_a * (ag_py/100) * g_to_oz) * (ag_p - ag_rc)
    v_au_pay = (au_a * (au_py/100) * g_to_oz) * (au_p - au_rc)
    d_cu = (cu_dv / 100) * cu_p
    d_ag = (ag_dv * g_to_oz) * ag_p
    d_au = (au_dv * g_to_oz) * au_p
    net = (v_cu_pay + v_ag_pay + v_au_pay) - (d_cu + d_ag + d_au) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. Sidebar & Global Inputs ---
with st.sidebar:
    st.header("💰 설정")
    mode = st.radio("거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

data = {} 
cases = [("A (Base)안", "a", 80.0), ("B안", "b", 80.0), ("C안", "c", 80.0)]

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

# --- 3. Tabs ---
tab1, tab2, tab3 = st.tabs(["📝 조건 입력", "📊 결과 비교", "🎯 협상 가이드"])

with tab1:
    for name, k, def_tc in cases:
        with st.expander(f"📍 {name} 상세 설정", expanded=(k=='a')):
            st.markdown(f"<div class='section-head'>Metals Setting</div>", unsafe_allow_html=True)
            # Cu
            data[f"cu_py_{k}"] = st.number_input(f"Cu Pay (%)", value=100.0, key=f"cp_{k}")
            data[f"cu_dt_{k}"] = st.radio(f"Cu Deduction Type", ["PD", "MD"], horizontal=True, key=f"cdt_{k}")
            data[f"cu_dv_{k}"] = st.number_input(f"Cu {data[f'cu_dt_{k}']} (%)", value=1.0, key=f"cdv_{k}")
            # Ag
            data[f"ag_py_{k}"] = st.number_input(f"Ag Pay (%)", value=90.0, key=f"ap_{k}")
            data[f"ag_dt_{k}"] = st.radio(f"Ag Deduction Type", ["PD", "MD"], horizontal=True, key=f"adt_{k}")
            data[f"ag_dv_{k}"] = st.number_input(f"Ag {data[f'ag_dt_{k}']} (g/t)", value=30.0, key=f"adv_{k}")
            # Au
            data[f"au_py_{k}"] = st.number_input(f"Au Pay (%)", value=90.0, key=f"aup_{k}")
            data[f"au_dt_{k}"] = st.radio(f"Au Deduction Type", ["PD", "MD"], horizontal=True, key=f"audt_{k}")
            data[f"au_dv_{k}"] = st.number_input(f"Au {data[f'au_dt_{k}']} (g/t)", value=1.0, key=f"audv_{k}")
            
            st.markdown(f"<div class='section-head'>Costs (TC/RC)</div>", unsafe_allow_html=True)
            data[f"tc_{k}"] = st.number_input(f"TC ($/t)", value=def_tc, key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input(f"Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
            data[f"ag_rc_{k}"] = st.number_input(f"Ag RC ($/oz)", value=0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input(f"Au RC ($/oz)", value=5.0, key=f"aurc_{k}")

# ★ 중요: 모든 입력이 끝난 후 계산을 수행 ★
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
    # B안에서 TC만 0으로 놓고 계산
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

    st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center;">
            <p style="margin: 0; color: #7f8c8d;">🎯 목표 TC (Target TC)</p>
            <p style="margin: 5px 0; font-size: 32px; font-weight: 800;">${be_tc:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)
    st.write(f"현재 B안 TC(${data['tc_b']:.2f}) 대비 **${abs(diff_tc):,.2f}** {'유리' if is_fav else '불리'}합니다.")

# --- 4. Calculation ---
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

with res_area.container():
    st.markdown("---")
    st.metric("A (비교기준값)", f"${abs(res['a']):,.2f} /t")
    st.metric("B안 이익 (vs A)", f"${abs(res['b']):,.2f} /t", f"{res['b'] - res['a']:,.2f}")
    st.metric("C안 이익 (vs A)", f"${abs(res['c']):,.2f} /t", f"{res['c'] - res['a']:,.2f}")

