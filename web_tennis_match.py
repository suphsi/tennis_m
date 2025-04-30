import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict
from itertools import combinations
import graphviz
from fpdf import FPDF

st.set_page_config(page_title="🎾 테니스 토너먼트 프로그램", layout="centered")
st.title("🎾 테니스 토너먼트 + 리그전 + 개인통계 + PDF 저장")

# 세션 초기화
for key in ["players", "matches", "mode", "match_type", "round_matches", "current_round", "final_scores", "game_history", "start_time", "score_record"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["players", "matches", "round_matches", "game_history"] else {}

st.session_state.setdefault("new_players", [])

# 참가자 입력
st.subheader("1. 참가자 등록")
with st.form("player_form", clear_on_submit=True):
    name = st.text_input("이름 입력")
    gender = st.radio("성별 선택", ["남", "여"], horizontal=True)
    submitted = st.form_submit_button("참가자 추가")
    if submitted and name:
        st.session_state.new_players.append({"name": name.strip(), "gender": gender})

if st.session_state.new_players:
    st.subheader("현재 참가자:")
    for i, p in enumerate(st.session_state.new_players):
        col1, col2 = st.columns([5,1])
        col1.markdown(f"- {p['name']} ({p['gender']})")
        if col2.button("❌", key=f"delete_{i}"):
            st.session_state.new_players.pop(i)
            st.rerun()

    st.divider()
    st.subheader("⚙️ 참가자 관리")
    if st.button("🚫 참가자 전체 초기화 요청"):
        if st.session_state.round_matches:
            st.warning("⚠️ 이미 대진표가 생성되었습니다.")
            confirm = st.radio("초기화 하시겠습니까?", ("초기화 취소", "초기화 진행"), index=0)
            if confirm == "초기화 진행":
                st.session_state.new_players.clear()
                st.session_state.players.clear()
                st.session_state.round_matches.clear()
                st.session_state.game_history.clear()
                st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
                st.success("✅ 전체 초기화가 완료되었습니다!")
                st.rerun()
            else:
                st.info("초기화가 취소되었습니다.")
        else:
            st.session_state.new_players.clear()
            st.session_state.players.clear()
            st.session_state.round_matches.clear()
            st.session_state.game_history.clear()
            st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
            st.success("✅ 참가자와 대진표가 초기화되었습니다!")
            st.rerun()

# 경기 설정
st.subheader("2. 경기 설정")
match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
mode = st.radio("진행 방식", ["리그전", "토너먼트"], horizontal=True)
game_per_player = st.number_input("리그전일 경우 1인당 경기 수", min_value=1, step=1, value=2)
num_courts = st.number_input("코트 수", min_value=1, step=1, value=2)
start_hour = st.time_input("경기 시작 시간 설정", value=datetime.time(10, 0))

def create_pairs(players):
    males = [p['name'] for p in players if p['gender'] == "남"]
    females = [p['name'] for p in players if p['gender'] == "여"]
    pairs = []
    random.shuffle(males)
    random.shuffle(females)
    for m, f in zip(males, females):
        pairs.append((m, f))
    return pairs

def generate_matches(players, match_type, mode):
    if match_type == "단식":
        candidates = [p['name'] for p in players]
    elif match_type == "복식":
        candidates = list(combinations([p['name'] for p in players], 2))
    elif match_type == "혼성 복식":
        candidates = create_pairs(players)
    else:
        candidates = []

    if mode == "리그전":
        all_matches = list(combinations(candidates, 2))
        random.shuffle(all_matches)
        return all_matches
    else:
        random.shuffle(candidates)
        return [(candidates[i], candidates[i+1]) if i+1 < len(candidates) else (candidates[i], "BYE") for i in range(0, len(candidates), 2)]

if st.button("🏆 토너먼트 시작!" if mode == "토너먼트" else "대진표 생성"):
    if len(st.session_state.new_players) < (2 if match_type == "단식" else 4):
        st.warning("참가자가 부족합니다.")
    else:
        st.session_state.players = st.session_state.new_players
        st.session_state.match_type = match_type
        st.session_state.mode = mode
        st.session_state.current_round = 1
        st.session_state.round_matches = generate_matches(st.session_state.players, match_type, mode)
        st.session_state.start_time = datetime.datetime.combine(datetime.date.today(), start_hour)
        st.session_state.game_history = []
        st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
        st.success("✅ 대진표가 생성되었습니다!")

# 대진표 미리보기 출력 추가
if st.session_state.round_matches:
    st.subheader("🎾 생성된 대진표")
    for i, match in enumerate(st.session_state.round_matches, 1):
        t1 = match[0] if isinstance(match[0], str) else " + ".join(match[0])
        t2 = match[1] if isinstance(match[1], str) else " + ".join(match[1])
        st.markdown(f"**{i}. {t1} vs {t2}**")

# 개인 통계 출력 및 MVP 표시
if st.session_state.score_record:
    st.subheader("📊 개인 통계")
    stat_data = []
    for player, record in st.session_state.score_record.items():
        total_games = record["승"] + record["패"]
        win_rate = (record["승"] / total_games * 100) if total_games else 0
        stat_data.append((player, record["승"], record["패"], record["득점"], record["실점"], f"{win_rate:.1f}%"))

    df_stats = pd.DataFrame(stat_data, columns=["이름", "승", "패", "득점", "실점", "승률"])
    df_stats = df_stats.sort_values(by=["승", "득점"], ascending=[False, False])
    df_stats.index += 1
    st.dataframe(df_stats, use_container_width=True)

    # 종합 MVP 표시
    if not df_stats.empty:
        st.subheader("🏅 종합 MVP (Top 3)")
        top3 = df_stats.head(3)
        medals = ["🥇 1위", "🥈 2위", "🥉 3위"]
        for idx, row in enumerate(top3.itertuples()):
            st.markdown(f"**{medals[idx]}: {row.이름}** (승: {row.승}, 득점: {row.득점}, 승률: {row.승률})")

    # PDF 저장
    if st.button("📥 결과 PDF로 저장하기"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "테니스 토너먼트 결과", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "개인 통계", ln=True)
        pdf.set_font("Arial", '', 10)
        for idx, row in df_stats.iterrows():
            line = f"{row['이름']} - 승: {row['승']} 패: {row['패']} 득점: {row['득점']} 실점: {row['실점']} 승률: {row['승률']}"
            pdf.cell(0, 8, line, ln=True)

        pdf_output = pdf.output(dest='S').encode('latin1')
        st.download_button(
            label="📄 PDF 다운로드",
            data=pdf_output,
            file_name="Tennis_Tournament_Result.pdf",
            mime="application/pdf"
        )
