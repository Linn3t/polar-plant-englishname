# ===============================
# 🌱 극지식물 최적 EC 농도 연구 대시보드
# Streamlit Cloud 대응 / 한글 파일명 NFC·NFD 완벽 처리
# ===============================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# ===============================
# 한글 폰트 (깨짐 방지)
# ===============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

PLOTLY_FONT = dict(
    family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"
)

# ===============================
# 상수 정의
# ===============================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,   # ⭐ 최적
    "아라고": 4.0,
    "동산고": 8.0
}

SCHOOL_COLOR = {
    "송도고": "#4C72B0",
    "하늘고": "#55A868",
    "아라고": "#C44E52",
    "동산고": "#8172B3"
}

# ===============================
# 파일명 정규화 유틸
# ===============================
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)

# ===============================
# 데이터 로딩 함수
# ===============================
@st.cache_data
def load_environment_data():
    data = {}
    if not DATA_DIR.exists():
        st.error("❌ data 폴더를 찾을 수 없습니다.")
        return data

    for file in DATA_DIR.iterdir():
        if file.suffix.lower() != ".csv":
            continue

        name = normalize(file.name)
        for school in SCHOOL_EC.keys():
            if normalize(school) in name:
                df = pd.read_csv(file)
                df["학교"] = school
                data[school] = df
    return data


@st.cache_data
def load_growth_data():
    if not DATA_DIR.exists():
        st.error("❌ data 폴더를 찾을 수 없습니다.")
        return pd.DataFrame()

    xlsx_file = None
    for file in DATA_DIR.iterdir():
        if file.suffix.lower() == ".xlsx":
            xlsx_file = file
            break

    if xlsx_file is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    xls = pd.ExcelFile(xlsx_file)
    frames = []

    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df["학교"] = sheet
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


# ===============================
# 데이터 로딩
# ===============================
with st.spinner("📡 데이터 불러오는 중..."):
    env_data = load_environment_data()
    growth_df = load_growth_data()

if not env_data or growth_df.empty:
    st.stop()

# ===============================
# 사이드바
# ===============================
st.sidebar.title("🏫 학교 선택")
school_option = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(SCHOOL_EC.keys())
)

# ===============================
# 제목
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")

# ===============================
# 탭 구성
# ===============================
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =========================================================
# 📖 TAB 1: 실험 개요
# =========================================================
with tab1:
    st.subheader("🔬 연구 배경 및 목적")
    st.markdown("""
    본 연구는 **극지식물의 생육에 미치는 EC(전기전도도) 농도의 영향**을 분석하여  
    **최적 EC 농도 조건**을 도출하는 것을 목적으로 한다.
    """)

    summary_rows = []
    for school, ec in SCHOOL_EC.items():
        count = len(growth_df[growth_df["학교"] == school])
        summary_rows.append([school, ec, count])

    summary_df = pd.DataFrame(
        summary_rows,
        columns=["학교명", "EC 목표", "개체수"]
    )

    st.subheader("🏫 학교별 EC 조건")
    st.dataframe(summary_df, use_container_width=True)

    total_count = len(growth_df)
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", f"{total_count} 개")
    c2.metric("평균 온도", f"{avg_temp:.1f} ℃")
    c3.metric("평균 습도", f"{avg_hum:.1f} %")
    c4.metric("최적 EC", "2.0 (하늘고) ⭐")

# =========================================================
# 🌡️ TAB 2: 환경 데이터
# =========================================================
with tab2:
    st.subheader("📊 학교별 환경 평균 비교")

    env_all = pd.concat(env_data.values(), ignore_index=True)

    mean_df = env_all.groupby("학교")[["temperature", "humidity", "ph", "ec"]].mean().reset_index()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=mean_df["학교"], y=mean_df["temperature"], row=1, col=1)
    fig.add_bar(x=mean_df["학교"], y=mean_df["humidity"], row=1, col=2)
    fig.add_bar(x=mean_df["학교"], y=mean_df["ph"], row=2, col=1)

    fig.add_bar(
        x=mean_df["학교"],
        y=[SCHOOL_EC[s] for s in mean_df["학교"]],
        name="목표 EC",
        row=2, col=2
    )
    fig.add_bar(
        x=mean_df["학교"],
        y=mean_df["ec"],
        name="실측 EC",
        row=2, col=2
    )

    fig.update_layout(height=700, font=PLOTLY_FONT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 환경 시계열 변화")

    if school_option != "전체":
        df = env_data[school_option]

        for col, title in [
            ("temperature", "온도 변화"),
            ("humidity", "습도 변화"),
            ("ec", "EC 변화")
        ]:
            fig = px.line(df, x="time", y=col, title=title)
            if col == "ec":
                fig.add_hline(y=SCHOOL_EC[school_option], line_dash="dash")
            fig.update_layout(font=PLOTLY_FONT)
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("📂 환경 데이터 원본"):
        st.dataframe(env_all)
        csv = env_all.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "CSV 다운로드",
            data=csv,
            file_name="환경데이터_전체.csv",
            mime="text/csv"
        )

# =========================================================
# 📊 TAB 3: 생육 결과
# =========================================================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    growth_df["EC"] = growth_df["학교"].map(SCHOOL_EC)
    mean_weight = growth_df.groupby("EC")["생중량(g)"].mean().reset_index()

    best_ec = mean_weight.loc[mean_weight["생중량(g)"].idxmax(), "EC"]

    cols = st.columns(len(mean_weight))
    for i, row in mean_weight.iterrows():
        label = "⭐ 최적" if row["EC"] == best_ec else ""
        cols[i].metric(
            f"EC {row['EC']}",
            f"{row['생중량(g)']:.2f} g",
            label
        )

    st.subheader("📊 EC별 생육 비교")

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수"]
    )

    fig.add_bar(x=mean_weight["EC"], y=mean_weight["생중량(g)"], row=1, col=1)

    leaf_mean = growth_df.groupby("EC")["잎 수(장)"].mean()
    fig.add_bar(x=leaf_mean.index, y=leaf_mean.values, row=1, col=2)

    shoot_mean = growth_df.groupby("EC")["지상부 길이(mm)"].mean()
    fig.add_bar(x=shoot_mean.index, y=shoot_mean.values, row=2, col=1)

    count_df = growth_df.groupby("EC").size()
    fig.add_bar(x=count_df.index, y=count_df.values, row=2, col=2)

    fig.update_layout(height=700, font=PLOTLY_FONT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📦 학교별 생중량 분포")
    fig = px.box(growth_df, x="학교", y="생중량(g)", color="학교")
    fig.update_layout(font=PLOTLY_FONT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔗 상관관계 분석")
    c1, c2 = st.columns(2)

    with c1:
        fig = px.scatter(
            growth_df, x="잎 수(장)", y="생중량(g)", color="학교",
            title="잎 수 vs 생중량"
        )
        fig.update_layout(font=PLOTLY_FONT)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(
            growth_df, x="지상부 길이(mm)", y="생중량(g)", color="학교",
            title="지상부 길이 vs 생중량"
        )
        fig.update_layout(font=PLOTLY_FONT)
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📂 생육 데이터 원본"):
        st.dataframe(growth_df)

        buffer = io.BytesIO()
        growth_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
