import streamlit as st
import random
import pandas as pd
from io import BytesIO
from itertools import combinations
from collections import defaultdict

st.set_page_config(page_title="🎾 테니스 대진표 앱", layout="centered")
st.title("🎾 테니스 대진표 프로그램")

# 세션 상태 초기화
for key in ["players", "matches", "scores", "past_matches"]:
    if key not in st.session_state:
        st.session_state[key] = []

# ✅ 1. 참가자 입력
st.subheader("1. 참가자 등록")

names_input = st.text_area("참가자 이름들을 쉼표(,)로 구분하여 입력하세요:", placeholder="예: 홍길동, 홍길동, 홍길동, 홍길동")

if names_input:
    st.session_state.players = [name.strip() for name in names_input.split(",") if name.strip()]
    st.success("현재 참가자: " + ", ".join(st.session_state.players))

# ✅ 2. 경기 수 설정 및 대진표 생성
st.subheader("2. 1인당 경기 수 지정 및 대진표 생성")

game_per_player = st.number_input("각 참가자가 몇 경기씩 하게 할까요?", min_value=1, step=1)

if len(st.session_state.players) >= 2:
    if st.button("대진표 생성 (1인당 N경기)"):
        players = st.session_state.players[:]
        all_matches = list(combinations(players, 2))
        random.shuffle(all_matches)

        match_counts = defaultdict(int)
        selected_matches = []

        for match in all_matches:
            p1, p2 = match
            if match_counts[p1] < game_per_player and match_counts[p2] < game_per_player:
                selected_matches.append(match)
                match_counts[p1] += 1
                match_counts[p2] += 1

        if all(count >= game_per_player for count in match_counts.values()):
            st.session_state.matches = selected_matches
            st.session_state.past_matches = selected_matches[:]
            st.session_state.scores = {}
            st.success("✅ 대진표가 생성되었습니다!")
        else:
            st.warning("⚠️ 현재 인원으로는 1인당 지정된 경기 수를 만족하는 대진표를 만들 수 없습니다.")
else:
    st.info("최소 2명 이상의 참가자가 필요합니다.")

# ✅ 3. 점수 입력 및 수정
if st.session_state.matches:
    st.subheader("3. 스코어 입력 및 수정")
    edited_scores = {}

    for idx, (p1, p2) in enumerate(st.session_state.matches):
        key = f"score_{idx}"
        default_score = st.session_state.get(key, "")
        score_input = st.text_input(f"{p1} vs {p2} (예: 2:1)", value=default_score, key=key)
        edited_scores[(p1, p2)] = score_input

    if st.button("🧮 점수 반영"):
        st.session_state.scores.clear()
        for (p1, p2), score in edited_scores.items():
            try:
                s1, s2 = map(int, score.strip().split(":"))
                st.session_state[f"score_{st.session_state.matches.index((p1, p2))}"] = score
                st.session_state.scores.setdefault(p1, 0)
                st.session_state.scores.setdefault(p2, 0)
                if s1 > s2:
                    st.session_state.scores[p1] += 3
                elif s1 < s2:
                    st.session_state.scores[p2] += 3
                else:
                    st.session_state.scores[p1] += 1
                    st.session_state.scores[p2] += 1
            except:
                st.warning(f"⚠️ {p1} vs {p2} 점수 입력 오류 (예: 2:1)")

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

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        score_df.to_excel(writer, index_label="순위", sheet_name="승점표")
    output.seek(0)

    st.download_button(
        label="📥 엑셀로 저장하기",
        data=output,
        file_name="tennis_scores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )