import streamlit as st
import random
from itertools import combinations, product
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="🎾 테니스 매치 메이커", layout="centered")
st.title("🎾 테니스 대진표 생성기")

match_type = st.selectbox("경기 유형을 선택하세요", ["단식", "복식", "혼성 복식"])
game_per_player = st.number_input("인당 경기 수", min_value=1, max_value=10, value=2)

st.subheader("1. 참가자 등록")
num_players = st.number_input("참가자 수 입력 (짝수)", min_value=2, step=1)
players = []

if match_type == "혼성 복식":
    gender_labels = ["남", "여"]
    for i in range(num_players):
        name = st.text_input(f"참가자 {i+1} 이름")
        gender = st.radio(f"성별 선택 ({i+1})", gender_labels, horizontal=True, key=f"gender_{i}")
        if name:
            players.append({"name": name.strip(), "gender": gender})
else:
    for i in range(num_players):
        name = st.text_input(f"참가자 {i+1} 이름")
        if name:
            players.append({"name": name.strip()})

st.markdown("---")

st.subheader("2. 대진표 생성")
if st.button("대진표 생성"):
    def generate_matches(match_type, game_per_player):
        if match_type == "단식":
            names = [p['name'] for p in players]
            all_matches = list(combinations(names, 2))
            random.shuffle(all_matches)
            match_counter = {name: 0 for name in names}
            matches = []
            for p1, p2 in all_matches:
                if match_counter[p1] < game_per_player or match_counter[p2] < game_per_player:
                    matches.append((p1, p2))
                    match_counter[p1] += 1
                    match_counter[p2] += 1
            return matches

        elif match_type == "복식":
            all_players = [p['name'] for p in players]
            all_pairs = list(combinations(all_players, 2))
            random.shuffle(all_pairs)
            used_players = set()
            team_pool = []
            for p1, p2 in all_pairs:
                if p1 not in used_players and p2 not in used_players:
                    team_pool.append((p1, p2))
                    used_players.update([p1, p2])
                if len(used_players) >= len(all_players):
                    break

            match_counter = {player: 0 for player in all_players}
            all_team_matches = list(combinations(team_pool, 2))
            random.shuffle(all_team_matches)
            matches = []
            for t1, t2 in all_team_matches:
                if set(t1) & set(t2):
                    continue
                p1, p2 = t1
                p3, p4 = t2
                if (match_counter[p1] < game_per_player or match_counter[p2] < game_per_player or
                    match_counter[p3] < game_per_player or match_counter[p4] < game_per_player):
                    matches.append((t1, t2))
                    for p in [p1, p2, p3, p4]:
                        match_counter[p] += 1
            return matches

        elif match_type == "혼성 복식":
            males = [p['name'] for p in players if p['gender'] == "남"]
            females = [p['name'] for p in players if p['gender'] == "여"]
            team_pool = list(product(males, females))
            random.shuffle(team_pool)
            match_counter = {name: 0 for name in males + females}
            matches = []
            used_teams = set()
            for t1, t2 in combinations(team_pool, 2):
                if t1 in used_teams or t2 in used_teams:
                    continue
                if set(t1) & set(t2):
                    continue
                p1, p2 = t1
                p3, p4 = t2
                if (match_counter[p1] < game_per_player or match_counter[p2] < game_per_player or
                    match_counter[p3] < game_per_player or match_counter[p4] < game_per_player):
                    matches.append((t1, t2))
                    used_teams.update([t1, t2])
                    for p in [p1, p2, p3, p4]:
                        match_counter[p] += 1
            return matches

    match_results = generate_matches(match_type, game_per_player)

    st.subheader("3. 생성된 대진표")
    if not match_results:
        st.warning("⚠️ 생성된 대진표가 없습니다. 참가자 수나 조건을 다시 확인하세요.")
    else:
        for idx, match in enumerate(match_results):
            if match_type == "단식":
                st.write(f"{idx+1} 경기: {match[0]} vs {match[1]}")
            else:
                team1 = " + ".join(match[0])
                team2 = " + ".join(match[1])
                st.write(f"{idx+1} 경기: {team1} vs {team2}")
