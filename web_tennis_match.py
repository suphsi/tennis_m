import streamlit as st
import random
import pandas as pd
from collections import defaultdict
from itertools import combinations
import time
import datetime

st.set_page_config(page_title="🎾 토너먼트 테니스 프로그램", layout="centered")
st.title("🎾 테니스 토너먼트 대진표")

# 세션 상태 초기화
for key in ["players", "matches", "mode", "match_type", "round_matches", "current_round", "final_scores", "game_history", "start_time"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["players", "matches", "round_matches", "game_history"] else {}

# ✅ 참가자 입력
st.subheader("1. 참가자 등록")
if "new_players" not in st.session_state:
    st.session_state.new_players = []

with st.form("player_form", clear_on_submit=True):
    name = st.text_input("이름 입력")
    gender = st.radio("성별 선택", ["남", "여"], horizontal=True)
    submitted = st.form_submit_button("추가하기")
    if submitted and name:
        st.session_state.new_players.append({"name": name.strip(), "gender": gender})

if st.session_state.new_players:
    st.success("현재 참가자:")
    for p in st.session_state.new_players:
        st.markdown(f"- {p['name']} ({p['gender']})")

# ✅ 경기 설정
st.subheader("2. 경기 설정")
match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
mode = st.radio("진행 방식", ["리그전", "토너먼트"], horizontal=True)
game_per_player = st.number_input("리그전일 경우 1인당 경기 수", min_value=1, step=1, value=2)
num_courts = st.number_input("코트 수", min_value=1, step=1, value=2)
start_hour = st.time_input("경기 시작 시간 설정", value=datetime.time(10, 0))

# ✅ 대진표 생성
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
    else:  # 토너먼트
        random.shuffle(candidates)
        return [(candidates[i], candidates[i+1]) if i+1 < len(candidates) else (candidates[i], "BYE") for i in range(0, len(candidates), 2)]

# ✅ 토너먼트 시작
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
        st.success("✅ 대진표가 생성되었습니다!")

# ✅ 대진표 및 점수 입력
if st.session_state.round_matches:
    st.subheader(f"Round {st.session_state.current_round} - 대진표 및 점수 입력")

    winners = []
    current_time = st.session_state.start_time

    for idx, match in enumerate(st.session_state.round_matches):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
        team1, team2 = match

        with col1:
            if isinstance(team1, tuple):
                st.markdown(f"**{team1[0]} + {team1[1]}**")
            else:
                st.markdown(f"**{team1}**")
        with col2:
            score1 = st.text_input(" ", key=f"s1_{idx}", label_visibility="collapsed")
        with col3:
            st.markdown("vs")
        with col4:
            score2 = st.text_input(" ", key=f"s2_{idx}", label_visibility="collapsed")
        with col5:
            if isinstance(team2, tuple):
                st.markdown(f"**{team2[0]} + {team2[1]}**")
            else:
                st.markdown(f"**{team2}**")

        # 경기 시간 표시
        st.caption(f"⏰ 경기 시간: {current_time.strftime('%H:%M')} ~ {(current_time + datetime.timedelta(minutes=10)).strftime('%H:%M')}")
        current_time += datetime.timedelta(minutes=10)

        # 결과 처리
        if team2 == "BYE":
            winners.append(team1)
            st.info(f"{team1} 부전승")
        elif score1 and score2:
            try:
                if int(score1) > int(score2):
                    winners.append(team1)
                    winner = team1
                elif int(score1) < int(score2):
                    winners.append(team2)
                    winner = team2
                else:
                    winner = random.choice([team1, team2])  # 무승부 랜덤 승자
                    winners.append(winner)

                st.session_state.game_history.append({
                    "라운드": st.session_state.current_round,
                    "팀1": team1 if isinstance(team1, str) else " + ".join(team1),
                    "팀2": team2 if isinstance(team2, str) else " + ".join(team2),
                    "점수": f"{score1}:{score2}",
                    "승자": winner if isinstance(winner, str) else " + ".join(winner)
                })

            except:
                st.warning("⚠️ 점수 입력 오류")

    if st.button("다음 라운드로 진행"):
        if len(winners) == 1:
            st.success(f"🏆 최종 MVP: {winners[0]}")
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
            st.experimental_rerun()

# ✅ 브래킷 트리 시각화
if st.session_state.game_history:
    st.subheader("📈 브래킷 트리")
    for game in st.session_state.game_history:
        st.markdown(f"**Round {game['라운드']}**: {game['팀1']} ({game['점수']}) {game['팀2']} ➡️ 승자: {game['승자']}")

# ✅ 경기별 상세 기록
if st.session_state.game_history:
    st.subheader("📝 경기별 상세 기록")
    df_history = pd.DataFrame(st.session_state.game_history)
    st.dataframe(df_history, use_container_width=True)
