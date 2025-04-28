import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict
from itertools import combinations
import graphviz
from fpdf import FPDF

st.set_page_config(page_title="🎾 테니스 대진표 프로그램", layout="centered")
st.title("🎾 테니스 대진표")

# 세션 초기화
for key in ["players", "matches", "mode", "match_type", "round_matches", "current_round", "final_scores", "game_history", "start_time", "score_record"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["players", "matches", "round_matches", "game_history"] else {}

# 참가자 입력
st.subheader("1. 참가자 등록")
if "new_players" not in st.session_state:
    st.session_state.new_players = []

with st.form("player_form", clear_on_submit=True):
    name = st.text_input("이름 입력")
    gender = st.radio("성별 선택", ["남", "여"], horizontal=True)
    submitted = st.form_submit_button("참가자 추가")
    if submitted and name:
        st.session_state.new_players.append({"name": name.strip(), "gender": gender})

# 참가자 리스트 출력 + 개별 삭제
if st.session_state.new_players:
    st.subheader("현재 참가자:")
    for i, p in enumerate(st.session_state.new_players):
        col1, col2 = st.columns([5,1])
        with col1:
            st.markdown(f"- {p['name']} ({p['gender']})")
        with col2:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.new_players.pop(i)
                st.rerun()

# 참가자 전체 초기화 버튼
if st.session_state.new_players:
    st.divider()
    st.subheader("⚙️ 참가자 관리")
    if st.button("🚫 참가자 전체 초기화 요청"):
        if st.session_state.round_matches:
            st.warning("⚠️ 이미 대진표가 생성되었습니다.")
            confirm = st.radio("초기화 하시겠습니까?", ("초기화 취소", "초기화 진행"), index=0)

            if confirm == "초기화 진행":
                st.session_state.new_players = []
                st.session_state.players = []
                st.session_state.round_matches = []
                st.session_state.game_history = []
                st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
                st.success("✅ 전체 초기화가 완료되었습니다!")
                st.rerun()
            else:
                st.info("초기화가 취소되었습니다.")
        else:
            st.session_state.new_players = []
            st.session_state.players = []
            st.session_state.round_matches = []
            st.session_state.game_history = []
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

# 대진표 및 점수 입력
if st.session_state.round_matches:
    st.subheader(f"Round {st.session_state.current_round} - 대진표 및 점수 입력")

    winners = []
    current_time = st.session_state.start_time

    for idx, match in enumerate(st.session_state.round_matches):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
        team1, team2 = match

        team1_name = team1 if isinstance(team1, str) else " + ".join(team1)
        team2_name = team2 if isinstance(team2, str) else " + ".join(team2)

        with col1:
            st.markdown(f"**{team1_name}**")
        with col2:
            score1 = st.text_input(" ", key=f"s1_{idx}", label_visibility="collapsed")
        with col3:
            st.markdown("vs")
        with col4:
            score2 = st.text_input(" ", key=f"s2_{idx}", label_visibility="collapsed")
        with col5:
            st.markdown(f"**{team2_name}**")

        st.caption(f"⏰ 경기 시간: {current_time.strftime('%H:%M')} ~ {(current_time + datetime.timedelta(minutes=10)).strftime('%H:%M')}")
        current_time += datetime.timedelta(minutes=10)

        if team2 == "BYE":
            winners.append(team1)
            st.info(f"{team1_name} 부전승")
        elif score1 and score2:
            try:
                s1, s2 = int(score1), int(score2)
                if s1 > s2:
                    winners.append(team1)
                    winner = team1
                elif s1 < s2:
                    winners.append(team2)
                    winner = team2
                else:
                    winner = random.choice([team1, team2])
                    winners.append(winner)

                st.session_state.game_history.append({
                    "라운드": st.session_state.current_round,
                    "팀1": team1_name,
                    "팀2": team2_name,
                    "점수": f"{s1}:{s2}",
                    "승자": team1_name if winner == team1 else team2_name
                })

                for p in (team1 if isinstance(team1, tuple) else [team1]):
                    st.session_state.score_record[p]["득점"] += s1
                    st.session_state.score_record[p]["실점"] += s2
                    if s1 > s2:
                        st.session_state.score_record[p]["승"] += 1
                    else:
                        st.session_state.score_record[p]["패"] += 1

                for p in (team2 if isinstance(team2, tuple) else [team2]):
                    st.session_state.score_record[p]["득점"] += s2
                    st.session_state.score_record[p]["실점"] += s1
                    if s2 > s1:
                        st.session_state.score_record[p]["승"] += 1
                    else:
                        st.session_state.score_record[p]["패"] += 1

            except:
                st.warning("⚠️ 점수 입력 오류")

    if st.button("다음 라운드로 진행"):
        if len(winners) == 1:
            st.success(f"🏆 최종 우승: {winners[0]}")
            st.session_state.round_matches = []
        else:
            next_round = []
            for i in range(0, len(winners), 2):
                if i+1 < len(winners):
                    next_round.append((winners[i], winners[i+1]))
                else:
                    next_round.append((winners[i], "BYE"))
            st.session_state.round_matches = next_round
            st.session_state.current_round += 1
            st.session_state.start_time += datetime.timedelta(minutes=10 * len(st.session_state.round_matches))
            st.rerun()

# 🏆 토너먼트 브래킷 출력 (토너먼트 모드일 때만!)
if st.session_state.game_history and st.session_state.mode == "토너먼트":
    st.subheader("🏆 토너먼트 브래킷")
    dot = graphviz.Digraph()

    for game in st.session_state.game_history:
        node1 = f"{game['팀1']} ({game['점수'].split(':')[0]})"
        node2 = f"{game['팀2']} ({game['점수'].split(':')[1]})"
        winner_node = f"{game['승자']}"
        dot.node(node1)
        dot.node(node2)
        dot.edge(node1, winner_node)
        dot.edge(node2, winner_node)

    st.graphviz_chart(dot)

# 📊 개인 통계 출력
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

# 🏅 개인 통계 기반 종합 MVP 1~3위 표시
if not df_stats.empty:
    st.subheader("🏅 종합 MVP (Top 3)")
    top3 = df_stats.head(3)
    medals = ["🥇 1위", "🥈 2위", "🥉 3위"]
    for idx, row in enumerate(top3.itertuples()):
        st.markdown(f"**{medals[idx]}: {row.이름}** (승: {row.승}, 득점: {row.득점}, 승률: {row.승률})")

# 📄 PDF 저장 기능
if st.session_state.game_history and st.button("📥 결과 PDF로 저장하기"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "테니스 토너먼트 결과", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "경기 결과", ln=True)
    pdf.set_font("Arial", '', 10)
    for game in st.session_state.game_history:
        line = f"Round {game['라운드']}: {game['팀1']} {game['점수']} {game['팀2']} ➔ 승자: {game['승자']}"
        pdf.cell(0, 8, line, ln=True)

    pdf.ln(8)

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
