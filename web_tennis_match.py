import streamlit as st
import random
import pandas as pd
from collections import defaultdict
from itertools import combinations
import time

st.set_page_config(page_title="🎾 테니스 대진표 앱", layout="centered")
st.title("🎾 테니스 대진표 프로그램")

# 세션 상태 초기화
for key in ["players", "matches", "scores", "final_scores"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["scores", "final_scores"] else []

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
        st.session_state.final_scores = {}
        st.success("✅ 대진표가 생성되었습니다!")
else:
    st.info("단식은 최소 2명, 복식은 최소 4명 이상 필요합니다.")

# ✅ 3. 표 형태 대진표 + 스코어 입력
if st.session_state.matches:
    st.subheader("3. 표 형태 대진표 + 점수 입력")
    num_courts = st.session_state.num_courts
    matches = st.session_state.matches
    schedule = [matches[i:i+num_courts] for i in range(0, len(matches), num_courts)]

    for round_idx, round_matches in enumerate(schedule):
        st.markdown(f"### Round {round_idx + 1}")
        cols = st.columns(num_courts)
        for court_idx, match in enumerate(round_matches):
            with cols[court_idx]:
                if st.session_state.match_type == "단식":
                    p1, p2 = match
                    label = f"{p1} vs {p2}"
                else:
                    team1, team2 = match
                    label = f"{' + '.join(team1)} vs {' + '.join(team2)}"
                st.markdown(f"**코트 {court_idx + 1}**")
                st.text(label)
                key = f"score_{round_idx}_{court_idx}"
                st.session_state.scores[key] = st.text_input("점수 (예: 2:1)", value=st.session_state.scores.get(key, ""), key=key)

    # ✅ 점수 반영 버튼
    if st.button("🧮 점수 반영 및 승점 계산"):
        scores = defaultdict(int)
        flat_matches = [match for round_matches in schedule for match in round_matches]

        for idx, match in enumerate(flat_matches):
            key = f"score_{idx // num_courts}_{idx % num_courts}"
            score = st.session_state.scores.get(key, "")
            try:
                s1_str, s2_str = score.strip().split(":")
                s1, s2 = int(s1_str), int(s2_str)
                if st.session_state.match_type == "단식":
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
                st.warning(f"⚠️ 점수 입력 오류 또는 형식 오류: {key}")

        st.session_state.final_scores = scores
        st.success("✅ 승점이 계산되었습니다!")

# ✅ 4. 승점표 출력
if st.session_state.final_scores:
    st.subheader("4. 승점표 (랭킹순)")
    sorted_scores = sorted(st.session_state.final_scores.items(), key=lambda x: x[1], reverse=True)
    df = pd.DataFrame(sorted_scores, columns=["이름", "승점"])
    df.index += 1
    st.dataframe(df)
    st.success("✅ 승점표가 갱신되었습니다!")
