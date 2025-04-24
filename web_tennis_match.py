import streamlit as st
import random
import pandas as pd

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

# 참가자 추가
st.subheader("1. 참가자 등록")
num_players = st.number_input("참가자 수 (짝수)", min_value=2, step=2)
if st.button("참가자 이름 입력"):
    st.session_state.players = []
    for i in range(num_players):
        name = st.text_input(f"{i+1}번째 참가자 이름", key=f"name_{i}")
        if name:
            st.session_state.players.append(name.strip())

if st.session_state.players:
    st.success("현재 참가자: " + ", ".join(st.session_state.players))

# 대진표 생성
st.subheader("2. 대진표 생성")
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
            pair = tuple(sorted((players[i], players[i+1])))
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
        st.success("대진표가 생성되었습니다!")
    else:
        st.error("중복 없는 대진표를 생성하지 못했습니다. 참가자를 바꿔보세요.")

# 대진표와 점수 입력
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
                st.warning("점수 형식이 잘못되었습니다. 예: 3:1")

# 승점표 출력
if st.session_state.scores:
    st.subheader("4. 승점표 (랭킹순)")
    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    score_df = pd.DataFrame(sorted_scores, columns=["이름", "승점"])
    score_df.index += 1
    st.dataframe(score_df)

    # 엑셀 저장
    st.download_button(
        label="📥 엑셀로 저장하기",
        data=score_df.to_excel(index_label="순위", engine="openpyxl"),
        file_name="tennis_scores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
