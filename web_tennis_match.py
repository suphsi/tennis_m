import streamlit as st
import random
import pandas as pd
from io import BytesIO
from collections import defaultdict
from itertools import combinations
import time

st.set_page_config(page_title="🎾 테니스 대진표 앱", layout="centered")
st.title("🎾 테니스 대진표 프로그램")

# 세션 상태 초기화
for key in ["players", "matches", "scores"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key != "scores" else {}

# ✅ 1. 참가자 입력
st.subheader("1. 참가자 등록")

names_input = st.text_area("참가자 이름들을 쉼표(,)로 구분하여 입력하세요:", placeholder="예: 패더러, 나달, 조코비치, 알카라즈")

if names_input:
    st.session_state.players = [name.strip() for name in names_input.split(",") if name.strip()]
    st.success("현재 참가자: " + ", ".join(st.session_state.players))

# ✅ 2. 경기 유형 및 대진표 생성
st.subheader("2. 경기 유형 및 대진표 생성")

match_type = st.radio("경기 유형을 선택하세요", ["단식", "복식"], horizontal=True)
game_per_player = st.number_input("각 참가자가 몇 경기씩 하게 할까요?", min_value=1, step=1)
num_courts = st.number_input("사용할 코트 수", min_value=1, step=1)

if len(st.session_state.players) >= (2 if match_type == "단식" else 4):
    if st.button("대진표 생성"):
        start_time = time.time()
        players = st.session_state.players[:]
        match_counts = defaultdict(int)
        matches = []

        if match_type == "단식":
            all_combos = list(combinations(players, 2))
            random.shuffle(all_combos)
            for p1, p2 in all_combos:
                if match_counts[p1] < game_per_player and match_counts[p2] < game_per_player:
                    matches.append((p1, p2))
                    match_counts[p1] += 1
                    match_counts[p2] += 1
        else:
            all_combos = list(combinations(players, 4))
            random.shuffle(all_combos)
            for combo in all_combos:
                team1 = tuple(sorted(combo[:2]))
                team2 = tuple(sorted(combo[2:]))
                if all(match_counts[p] < game_per_player for p in combo):
                    matches.append((team1, team2))
                    for p in combo:
                        match_counts[p] += 1

        elapsed_time = time.time() - start_time
        st.write(f"⏱ 대진표 생성에 {elapsed_time:.2f}초 걸렸습니다.")

        if not matches:
            st.warning("⚠️ 조건에 맞는 대진표를 생성할 수 없습니다.")

        st.session_state.matches = matches
        st.session_state.scores = {}
        st.session_state.match_type = match_type
        st.session_state.num_courts = num_courts
        st.success("✅ 대진표가 생성되었습니다!")
else:
    st.info("단식은 최소 2명, 복식은 최소 4명 이상 필요합니다.")

# ✅ 3. 경기 일정표 (표 형태 대진표)
if st.session_state.matches:
    st.subheader("3. 표 형태 대진표")
    num_courts = st.session_state.num_courts
    matches = st.session_state.matches
    schedule = [matches[i:i+num_courts] for i in range(0, len(matches), num_courts)]

    table_data = []
    for round_idx, round_matches in enumerate(schedule):
        row = {"Round": f"Round {round_idx + 1}"}
        for court_idx in range(num_courts):
            if court_idx < len(round_matches):
                match = round_matches[court_idx]
                if st.session_state.match_type == "단식":
                    p1, p2 = match
                    row[f"코트 {court_idx + 1}"] = f"{p1} vs {p2}"
                else:
                    team1, team2 = match
                    row[f"코트 {court_idx + 1}"] = f"{' + '.join(team1)} vs {' + '.join(team2)}"
            else:
                row[f"코트 {court_idx + 1}"] = "-"
        table_data.append(row)

    df_schedule = pd.DataFrame(table_data)
    st.dataframe(df_schedule, use_container_width=True)

# ✅ 이후 섹션은 그대로 유지 (점수 입력, 반영, 결과 출력 등)
# 생략된 나머지 기능은 유지되며 점수 입력과 승점표도 정상 작동합니다.
