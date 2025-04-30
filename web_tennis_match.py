# ✅ 테니스 토너먼트 전체 코드 (점수 입력 포함 버전)
import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict
from itertools import combinations

st.set_page_config(page_title="🎾 테니스 토너먼트", layout="wide")
st.title("🎾 테니스 리그/토너먼트 매치 시스템")

# --- 초기 세션값 설정 ---
keys = ["players", "matches", "mode", "match_type", "round_matches", "current_round", "final_scores", "game_history", "start_time", "score_record"]
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ["players", "matches", "round_matches", "game_history"] else {}

st.session_state.setdefault("new_players", [])

# --- 참가자 입력 ---
st.subheader("1. 참가자 등록")
with st.form("add_player", clear_on_submit=True):
    name = st.text_input("이름 입력")
    gender = st.radio("성별", ["남", "여"], horizontal=True)
    submitted = st.form_submit_button("추가")
    if submitted and name:
        st.session_state.new_players.append({"name": name.strip(), "gender": gender})

if st.session_state.new_players:
    st.subheader("✅ 현재 참가자 목록")
    for i, p in enumerate(st.session_state.new_players):
        col1, col2 = st.columns([5, 1])
        col1.markdown(f"- {p['name']} ({p['gender']})")
        if col2.button("❌", key=f"del_{i}"):
            st.session_state.new_players.pop(i)
            st.rerun()

    if st.button("🚫 참가자 전체 초기화"):
        st.session_state.new_players.clear()
        st.session_state.players.clear()
        st.session_state.round_matches.clear()
        st.session_state.score_record.clear()
        st.session_state.game_history.clear()
        st.rerun()

# --- 설정 ---
st.subheader("2. 경기 설정")
match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
mode = st.radio("진행 방식", ["리그전", "토너먼트"], horizontal=True)
start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0))

# --- 매치 생성 함수 ---
def create_pairs(players):
    males = [p['name'] for p in players if p['gender'] == "남"]
    females = [p['name'] for p in players if p['gender'] == "여"]
    pairs = []
    for m, f in zip(males, females):
        pairs.append((m, f))
    return pairs

def generate_matches(players, match_type):
    if match_type == "단식":
        names = [p['name'] for p in players]
    elif match_type == "복식":
        names = list(combinations([p['name'] for p in players], 2))
    elif match_type == "혼성 복식":
        names = create_pairs(players)
    else:
        names = []
    return list(combinations(names, 2))

# --- 대진표 생성 ---
if st.button("🎯 대진표 생성"):
    if len(st.session_state.new_players) < 2:
        st.warning("2명 이상 필요합니다.")
    else:
        st.session_state.players = st.session_state.new_players.copy()
        st.session_state.round_matches = generate_matches(st.session_state.players, match_type)
        st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
        st.session_state.game_history.clear()
        st.success("✅ 대진표가 생성되었습니다.")
        st.rerun()

# --- 대진표 + 점수 입력 ---
if st.session_state.round_matches:
    st.subheader("3. 대진표 및 점수 입력")
    for idx, match in enumerate(st.session_state.round_matches):
        team1, team2 = match
        t1 = team1 if isinstance(team1, str) else " + ".join(team1)
        t2 = team2 if isinstance(team2, str) else " + ".join(team2)

        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
        col1.markdown(f"**{t1}**")
        s1 = col2.text_input(" ", key=f"s1_{idx}", label_visibility="collapsed")
        col3.markdown("vs")
        s2 = col4.text_input(" ", key=f"s2_{idx}", label_visibility="collapsed")
        col5.markdown(f"**{t2}**")

    if st.button("✅ 점수 반영"):
        for idx, match in enumerate(st.session_state.round_matches):
            team1, team2 = match
            key1 = f"s1_{idx}"
            key2 = f"s2_{idx}"
            val1 = st.session_state.get(key1, "").strip()
            val2 = st.session_state.get(key2, "").strip()
            if not val1 or not val2 or not val1.isdigit() or not val2.isdigit():
                continue
            s1, s2 = int(val1), int(val2)
            t1_list = team1 if isinstance(team1, tuple) else [team1]
            t2_list = team2 if isinstance(team2, tuple) else [team2]

            for p in t1_list:
                st.session_state.score_record[p]["득점"] += s1
                st.session_state.score_record[p]["실점"] += s2
            for p in t2_list:
                st.session_state.score_record[p]["득점"] += s2
                st.session_state.score_record[p]["실점"] += s1
            if s1 > s2:
                for p in t1_list:
                    st.session_state.score_record[p]["승"] += 1
                for p in t2_list:
                    st.session_state.score_record[p]["패"] += 1
            elif s2 > s1:
                for p in t2_list:
                    st.session_state.score_record[p]["승"] += 1
                for p in t1_list:
                    st.session_state.score_record[p]["패"] += 1
        st.success("✅ 점수가 반영되었습니다.")

# --- 결과 요약 ---
if st.session_state.score_record:
    st.subheader("📊 결과 요약 및 종합 MVP")
    stats = []
    for name, r in st.session_state.score_record.items():
        total = r['승'] + r['패']
        rate = f"{r['승']/total*100:.1f}%" if total else "0%"
        stats.append((name, r['승'], r['패'], r['득점'], r['실점'], rate))

    df = pd.DataFrame(stats, columns=["이름", "승", "패", "득점", "실점", "승률"])
    df = df.sort_values(by=["승", "득점"], ascending=[False, False])
    df.index += 1
    st.dataframe(df, use_container_width=True)

    st.markdown("### 🏅 MVP Top 3")
    for i, row in df.head(3).iterrows():
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else ""
        st.markdown(f"**{medal} {row['이름']}** - 승 {row['승']}, 승률 {row['승률']}")

        pdf_output = pdf.output(dest='S').encode('latin1')
        st.download_button(
            label="📄 PDF 다운로드",
            data=pdf_output,
            file_name="Tennis_Tournament_Result.pdf",
            mime="application/pdf"
        )
