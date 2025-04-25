import streamlit as st
import random
import pandas as pd
from collections import defaultdict
from itertools import combinations
import time

st.set_page_config(page_title="🎾 테니스 대진표 앱", layout="centered")
st.title("🎾 테니스 병렬 대진표 프로그램")

# 초기화
for key in ["players", "matches", "scores", "final_scores"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["scores", "final_scores"] else []

# 참가자 입력
st.subheader("1. 참가자 등록")
names_input = st.text_area("참가자 이름을 쉼표(,)로 구분하여 입력하세요:", placeholder="예: 패더러, 나달, 조코비치")
if names_input:
    st.session_state.players = [name.strip() for name in names_input.split(",") if name.strip()]
    st.success("현재 참가자: " + ", ".join(st.session_state.players))

# 대진 생성
st.subheader("2. 경기 설정 및 대진표 생성")
match_type = st.radio("경기 유형", ["단식", "복식"], horizontal=True)
game_per_player = st.number_input("1인당 경기 수", min_value=1, value=2)
num_courts = st.number_input("코트 수", min_value=1, value=2)

if len(st.session_state.players) >= (2 if match_type == "단식" else 4):
    if st.button("대진표 생성"):
        players = st.session_state.players[:]
        match_counts = defaultdict(int)
        matches = []
        if match_type == "단식":
            combos = list(combinations(players, 2))
            random.shuffle(combos)
            for p1, p2 in combos:
                if match_counts[p1] < game_per_player and match_counts[p2] < game_per_player:
                    matches.append((p1, p2))
                    match_counts[p1] += 1
                    match_counts[p2] += 1
        else:
            combos = list(combinations(players, 4))
            random.shuffle(combos)
            for combo in combos:
                team1 = tuple(sorted(combo[:2]))
                team2 = tuple(sorted(combo[2:]))
                if all(match_counts[p] < game_per_player for p in combo):
                    matches.append((team1, team2))
                    for p in combo:
                        match_counts[p] += 1

        st.session_state.matches = matches
        st.session_state.scores = {}
        st.session_state.match_type = match_type
        st.session_state.num_courts = num_courts
        st.session_state.final_scores = {}
        st.success("✅ 대진표가 생성되었습니다!")

# 병렬 구조 대진표 + 점수 입력
if st.session_state.matches:
    st.subheader("3. 대진표 + 점수 입력")
    num_courts = st.session_state.num_courts
    matches = st.session_state.matches
    schedule = [matches[i:i+num_courts] for i in range(0, len(matches), num_courts)]

    for round_idx, round_matches in enumerate(schedule):
        st.markdown(f"### 🕐 Round {round_idx + 1}")
        for court_idx, match in enumerate(round_matches):
            cols = st.columns([1, 1, 1, 1, 2])

            if match_type == "단식":
                team1, team2 = match
                team1_name = team1
                team2_name = team2
            else:
                team1, team2 = match
                team1_name = " + ".join(team1)
                team2_name = " + ".join(team2)

            key1 = f"r{round_idx}_c{court_idx}_1"
            key2 = f"r{round_idx}_c{court_idx}_2"

            with cols[0]:
                st.markdown(f"**{team1_name}**")
            with cols[1]:
                st.session_state.scores[key1] = st.text_input(" ", value=st.session_state.scores.get(key1, ""), key=key1, label_visibility="collapsed")
            with cols[2]:
                st.markdown("<div style='text-align: center;'>vs</div>", unsafe_allow_html=True)
            with cols[3]:
                st.session_state.scores[key2] = st.text_input(" ", value=st.session_state.scores.get(key2, ""), key=key2, label_visibility="collapsed")
            with cols[4]:
                st.markdown(f"**{team2_name}**")

# 점수 반영
    if st.button("🧮 점수 반영 및 승점 계산"):
        scores = defaultdict(int)
        for round_idx, round_matches in enumerate(schedule):
            for court_idx, match in enumerate(round_matches):
                key1 = f"r{round_idx}_c{court_idx}_1"
                key2 = f"r{round_idx}_c{court_idx}_2"
                try:
                    s1 = int(st.session_state.scores.get(key1, "0"))
                    s2 = int(st.session_state.scores.get(key2, "0"))
                    if match_type == "단식":
                        p1, p2 = match
                        if s1 > s2:
                            scores[p1] += 3
                        elif s1 < s2:
                            scores[p2] += 3
                        else:
                            scores[p1] += 1
                            scores[p2] += 1
                    else:
                        team1, team2 = match
                        if s1 > s2:
                            for p in team1:
                                scores[p] += 3
                        elif s1 < s2:
                            for p in team2:
                                scores[p] += 3
                        else:
                            for p in team1 + team2:
                                scores[p] += 1
                except:
                    st.warning(f"⚠️ Round {round_idx+1}, 코트 {court_idx+1} 점수 입력 오류")

        st.session_state.final_scores = scores
        st.success("✅ 승점이 계산되었습니다!")

# 승점표 출력 + MVP 선정
if st.session_state.final_scores:
    st.subheader("4. 승점표 (랭킹순)")
    sorted_scores = sorted(st.session_state.final_scores.items(), key=lambda x: x[1], reverse=True)
    df = pd.DataFrame(sorted_scores, columns=["이름", "승점"])
    df.index += 1
    st.dataframe(df, use_container_width=True)

    # MVP 선정
    if sorted_scores:
        mvp_name, mvp_score = sorted_scores[0]
        st.success(f"🏆 MVP: {mvp_name} ({mvp_score}점)")
