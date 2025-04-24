import streamlit as st
import random
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🎾 테니스 대진표 앱", layout="centered")
st.title("🎾 테니스 대진표 프로그램")

# 세션 상태 초기화
if "players" not in st.session_state:
    st.session_state.players = []
if "matches" not in st.session_state:
    st.session_state.matches = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "past_matches" not in st.session_state:
    st.session_state.past_matches = set()

# ✅ 1. 참가자 입력
st.subheader("1. 참가자 등록")

names_input = st.text_area("참가자 이름들을 쉼표(,)로 구분하여 입력하세요:", placeholder="예: Blake, Eunsu, Sara, Jin")

if names_input:
    st.session_state.players = [name.strip() for name in names_input.split(",") if name.strip()]
    st.success("현재 참가자: " + ", ".join(st.session_state.players))

# ✅ 2. 대진표 생성
st.subheader("2. 대진표 생성")

if len(st.session_state.players) >= 2 and len(st.session_state.players) % 2 == 0:
    if st.button("대진표 무작위 생성"):
        players = st.session_state.players[:]
        random.shuffle(players)
        matches = []
        attempts = 0
        max_attempts = 100
        while attempts < max_attempts:
            valid = True
            trial_matches = []
            for i in range(0, len(players), 2):
                pair = tuple(sorted((players[i], players[i + 1])))
                if pair in st.session_state.past_matches:
                    valid = False
                    break
                trial_matches.append(pair)
            if valid:
                matches = trial_matches
                break
            random.shuffle(players)
            attempts += 1

        if matches:
            st.session_state.matches = matches
            for pair in matches:
                st.session_state.past_matches.add(pair)
            st.success("✅ 대진표가 생성되었습니다!")
        else:
            st.error("⚠️ 중복 없는 대진표를 생성하지 못했습니다. 참가자를 바꿔보세요.")
else:
    st.info("짝수의 참가자를 입력해주세요.")

# ✅ 3. 대진표와 점수 입력
if st.session_state.matches:
    st.subheader("3. 스코어 입력 및 승점 계산")

    for idx, (p1, p2) in enumerate(st.session_state.matches):
        score = st.text_input(f"{p1} vs {p2} (예: 3:1)", key=f"score_{idx}")
        if score:
            try:
                s1, s2 = map(int, score.strip().split(":"))
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
                st.warning("❗ 점수 형식이 잘못되었습니다. 예: 3:1")

# ✅ 4. 승점표 출력
if st.session_state.scores:
    st.subheader("4. 승점표 (랭킹순)")
    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    score_df = pd.DataFrame(sorted_scores, columns=["이름", "승점"])
    score_df.index += 1
    st.dataframe(score_df)

    # ✅ 엑셀 다운로드
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
