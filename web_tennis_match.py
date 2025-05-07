import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
from itertools import combinations, product
from collections import defaultdict

st.set_page_config(page_title="🎾 테니스 매치 메이커", layout="centered")
st.title("🎾 테니스 대진표 생성기")

match_type = st.selectbox("경기 유형을 선택하세요", ["단식", "복식", "혼성 복식"])
game_per_player = st.number_input("인당 경기 수", min_value=1, max_value=10, value=2)

players = []
st.subheader("1. 참가자 등록")
num_players = st.number_input("참가자 수 입력 (짝수)", min_value=2, step=2)

if 'player_names' not in st.session_state:
    st.session_state.player_names = []

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
            last_played_round = {name: -99 for name in names}
            matches = []

            round_num = 0
            for p1, p2 in all_matches:
                if match_counter[p1] < game_per_player and match_counter[p2] < game_per_player:
                    if round_num - last_played_round[p1] < 2 or round_num - last_played_round[p2] < 2:
                        continue
                    matches.append((p1, p2))
                    match_counter[p1] += 1
                    match_counter[p2] += 1
                    last_played_round[p1] = round_num
                    last_played_round[p2] = round_num
                    round_num += 1
            return matches

        elif match_type == "복식":
            all_players = [p['name'] for p in players]
            all_pairs = list(combinations(all_players, 2))
            random.shuffle(all_pairs)
            team_pool = [(p1, p2) for p1, p2 in all_pairs if p1 != p2]
            all_team_matches = list(combinations(team_pool, 2))
            random.shuffle(all_team_matches)
            match_counter = {player: 0 for player in all_players}
            last_played_round = {player: -99 for player in all_players}
            matches = []
            round_num = 0

            for t1, t2 in all_team_matches:
                if set(t1) & set(t2):
                    continue
                all_players_in_match = set(t1 + t2)
                if any(round_num - last_played_round[p] < 2 for p in all_players_in_match):
                    continue
                if all(match_counter[p] < game_per_player for p in all_players_in_match):
                    matches.append((t1, t2))
                    for p in all_players_in_match:
                        match_counter[p] += 1
                        last_played_round[p] = round_num
                    round_num += 1
            return matches

        elif match_type == "혼성 복식":
            males = [p['name'] for p in players if p['gender'] == "남"]
            females = [p['name'] for p in players if p['gender'] == "여"]
            team_pool = list(product(males, females))
            all_team_matches = list(combinations(team_pool, 2))
            random.shuffle(all_team_matches)
            match_counter = {name: 0 for name in males + females}
            last_played_round = {name: -99 for name in males + females}
            matches = []
            used_teams = set()
            round_num = 0

            for t1, t2 in all_team_matches:
                if t1 in used_teams or t2 in used_teams:
                    continue
                if set(t1) & set(t2):
                    continue
                all_players_in_match = set(t1 + t2)
                if any(round_num - last_played_round[p] < 2 for p in all_players_in_match):
                    continue
                if all(match_counter[p] < game_per_player for p in all_players_in_match):
                    matches.append((t1, t2))
                    used_teams.update([t1, t2])
                    for p in all_players_in_match:
                        match_counter[p] += 1
                        last_played_round[p] = round_num
                    round_num += 1
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
            recent_players = []
            for t1, t2 in all_team_matches:
                if set(t1) & set(t2):
                    continue
                all_in_match = set(t1 + t2)
                if any(p in recent_players[-8:] for p in all_in_match):
                    continue
                p1, p2 = t1
                p3, p4 = t2
                if (match_counter[p1] < game_per_player or match_counter[p2] < game_per_player or
                    match_counter[p3] < game_per_player or match_counter[p4] < game_per_player):
                    matches.append((t1, t2))
                    for p in all_in_match:
                        match_counter[p] += 1
                        recent_players.append(p)
            return matches

        elif match_type == "혼성 복식":
            males = [p['name'] for p in players if p['gender'] == "남"]
            females = [p['name'] for p in players if p['gender'] == "여"]
            team_pool = list(product(males, females))
            random.shuffle(team_pool)
            match_counter = {name: 0 for name in males + females}
            matches = []
            recent_players = []
            used_teams = set()
            for t1, t2 in combinations(team_pool, 2):
                if t1 in used_teams or t2 in used_teams:
                    continue
                if set(t1) & set(t2):
                    continue
                all_players_in_match = set(t1 + t2)
                if any(p in recent_players[-8:] for p in all_players_in_match):
                    continue
                p1, p2 = t1
                p3, p4 = t2
                if (match_counter[p1] < game_per_player or match_counter[p2] < game_per_player or
                    match_counter[p3] < game_per_player or match_counter[p4] < game_per_player):
                    matches.append((t1, t2))
                    used_teams.update([t1, t2])
                    for p in all_players_in_match:
                        match_counter[p] += 1
                        recent_players.append(p)
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
            player_last_round = {name: -2 for name in all_players}
            for round_num, (t1, t2) in enumerate(all_team_matches):
                if set(t1) & set(t2):
                    continue
                all_players_in_match = set(t1 + t2)
                if any(round_num - player_last_round[p] < 2 for p in all_players_in_match):
                    continue
                p1, p2 = t1
                p3, p4 = t2
                if (match_counter[p1] < game_per_player or match_counter[p2] < game_per_player or
                    match_counter[p3] < game_per_player or match_counter[p4] < game_per_player):
                    matches.append((t1, t2))
                    for p in all_players_in_match:
                        match_counter[p] += 1
                        player_last_round[p] = round_num
            return matches

        elif match_type == "혼성 복식":
            males = [p['name'] for p in players if p['gender'] == "남"]
            females = [p['name'] for p in players if p['gender'] == "여"]
            team_pool = list(product(males, females))
            random.shuffle(team_pool)
            match_counter = {name: 0 for name in males + females}
            matches = []
            used_teams = set()
            player_last_round = {name: -2 for name in males + females}
            for round_num, (t1, t2) in enumerate(combinations(team_pool, 2)):
                if t1 in used_teams or t2 in used_teams:
                    continue
                if set(t1) & set(t2):
                    continue
                all_players_in_match = set(t1 + t2)
                if any(round_num - player_last_round[p] < 2 for p in all_players_in_match):
                    continue
                p1, p2 = t1
                p3, p4 = t2
                if (match_counter[p1] < game_per_player or match_counter[p2] < game_per_player or
                    match_counter[p3] < game_per_player or match_counter[p4] < game_per_player):
                    matches.append((t1, t2))
                    used_teams.update([t1, t2])
                    for p in all_players_in_match:
                        match_counter[p] += 1
                        player_last_round[p] = round_num
            return matches

    match_results = generate_matches(match_type, game_per_player)
    st.subheader("3. 생성된 대진표")
    score_inputs = []
    if not match_results:
        st.warning("⚠️ 생성된 대진표가 없습니다. 참가자 수나 조건을 다시 확인하세요.")
    else:
        for idx, match in enumerate(match_results):
            col1, col2, col3 = st.columns([4, 1, 4])
            if match_type == "단식":
                p1, p2 = match
                with col1:
                    st.write(p1)
                    s1 = st.text_input("", key=f"s1_{idx}", label_visibility="collapsed")
                with col2:
                    st.write("vs")
                with col3:
                    st.write(p2)
                    s2 = st.text_input("", key=f"s2_{idx}", label_visibility="collapsed")
                score_inputs.append(((p1, p2), s1, s2))
            else:
                team1 = " + ".join(match[0])
                team2 = " + ".join(match[1])
                with col1:
                    st.write(team1)
                    s1 = st.text_input("", key=f"s1_{idx}", label_visibility="collapsed")
                with col2:
                    st.write("vs")
                with col3:
                    st.write(team2)
                    s2 = st.text_input("", key=f"s2_{idx}", label_visibility="collapsed")
                score_inputs.append(((team1, team2), s1, s2))

        if st.button("점수 반영"):
            score_board = defaultdict(int)
            for (p1, p2), s1, s2 in score_inputs:
                try:
                    s1 = int(s1)
                    s2 = int(s2)
                except:
                    st.warning(f"점수 입력 오류 ({p1} vs {p2})")
                    continue

                if s1 > s2:
                    score_board[p1] += 3
                elif s1 < s2:
                    score_board[p2] += 3
                else:
                    score_board[p1] += 1
                    score_board[p2] += 1

            st.subheader("🏆 승점 랭킹")
            sorted_scores = sorted(score_board.items(), key=lambda x: x[1], reverse=True)
            for rank, (name, pts) in enumerate(sorted_scores, 1):
                st.write(f"{rank}. {name}: {pts}점")

            if sorted_scores:
                st.subheader("🎖️ MVP")
                for i, (name, pts) in enumerate(sorted_scores[:3], 1):
                    st.write(f"MVP {i}: {name} ({pts}점)")
        for idx, match in enumerate(match_results):
            if match_type == "단식":
                st.write(f"{idx+1} 경기: {match[0]} vs {match[1]}")
            else:
                team1 = " + ".join(match[0])
                team2 = " + ".join(match[1])
                st.write(f"{idx+1} 경기: {team1} vs {team2}")
