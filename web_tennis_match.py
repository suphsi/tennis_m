import streamlit as st
import random
import pandas as pd
from io import BytesIO
from collections import defaultdict
from itertools import combinations
import time

st.set_page_config(page_title="🎾 테니스 대진표 앱", layout="centered")
st.title("🎾 테니스 대진표 프로그램 (조합 기반 속도 개선)")

# 세션 상태 초기화
for key in ["players", "matches", "scores"]:
    if key not in st.session_state:
        st.session_state[key] = []

# ✅ 1. 참가자 입력
st.subheader("1. 참가자 등록")

names_input = st.text_area("참가자 이름들을 쉼표(,)로 구분하여 입력하세요:", placeholder="예: Blake, Eunsu, Sara, Jin")

if names_input:
    st.session_state.players = [name.strip() for name in names_input.split(",") if name.strip()]
    st.success("현재 참가자: " + ", ".join(st.session_state.players))

# ✅ 2. 경기 유형 선택 및 대진표 생성
st.subheader("2. 경기 유형 및 대진표 생성")

match_type = st.radio("경기 유형을 선택하세요", ["단식", "복식"], horizontal=True)
game_per_player = st.number_input("각 참가자가 몇 경기씩 하게 할까요?", min_value=1, step=1)

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
        st.success("✅ 대진표가 생성되었습니다!")
else:
    st.info("단식은 최소 2명, 복식은 최소 4명 이상 필요합니다.")

# ✅ 3. 점수 입력 및 수정
if st.session_state.matches:
    st.subheader("3. 스코어 입력 및 수정")
    edited_scores = {}
    cols = st.columns(2)

    for idx, match in enumerate(st.session_state.matches):
        key = f"score_{idx}"
        default_score = st.session_state.get(key, "")

        if st.session_state.match_type == "단식":
            p1, p2 = match
            label = f"Round {idx + 1}: {p1} vs {p2}"
        else:
            (p1a, p1b), (p2a, p2b) = match
            label = f"Round {idx + 1}: {p1a}+{p1b} vs {p2a}+{p2b}"

        with cols[idx % 2]:
            score_input = st.text_input(label, value=default_score, key=key)
        edited_scores[(match, idx)] = score_input

    if st.button("🧮 점수 반영"):
        st.session_state.scores.clear()
        for (match, idx), score in edited_scores.items():
            try:
                s1, s2 = map(int, score.strip().split(":"))
                st.session_state[f"score_{idx}"] = score

                if st.session_state.match_type == "단식":
                    p1, p2 = match
                    st.session_state.scores.setdefault(p1, 0)
                    st.session_state.scores.setdefault(p2, 0)
                    if s1 > s2:
                        st.session_state.scores[p1] += 3
                    elif s1 < s2:
                        st.session_state.scores[p2] += 3
                    else:
                        st.session_state.scores[p1] += 1
                        st.session_state.scores[p2] += 1

                else:
                    team1, team2 = match
                    for p in team1 + team2:
                        st.session_state.scores.setdefault(p, 0)
                    if s1 > s2:
                        for p in team1:
                            st.session_state.scores[p] += 3
                    elif s1 < s2:
                        for p in team2:
                            st.session_state.scores[p] += 3
                    else:
                        for p in team1 + team2:
                            st.session_state.scores[p] += 1

            except:
                st.warning(f"⚠️ 점수 입력 오류 (예: 2:1)")

    if st.button("🔄 점수 전체 초기화"):
        for idx in range(len(st.session_state.matches)):
            st.session_state[f"score_{idx}"] = ""
        st.session_state.scores.clear()
        st.success("모든 점수가 초기화되었습니다!")

# ✅ 4. 승점표 출력 및 엑셀 다운로드
if st.session_state.scores:
    st.subheader("4. 승점표 (랭킹순)")
    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    score_df = pd.DataFrame(sorted_scores, columns=["이름", "승점"])
    score_df.index += 1
    st.dataframe(score_df)

    match_data = []
    for i, match in enumerate(st.session_state.matches):
        if st.session_state.match_type == "단식":
            p1, p2 = match
            match_data.append((f"Round {i+1}", p1, p2))
        else:
            team1, team2 = match
            match_data.append((f"Round {i+1}", "+".join(team1), "+".join(team2)))

    match_df = pd.DataFrame(match_data, columns=["라운드", "팀1", "팀2"])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        score_df.to_excel(writer, index_label="순위", sheet_name="승점표")
        match_df.to_excel(writer, index=False, sheet_name="대진표")
    output.seek(0)

    st.download_button(
        label="📥 엑셀로 저장하기",
        data=output,
        file_name="tennis_scores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
