import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict

st.set_page_config(page_title="🎾 테니스 매치 시스템", layout="centered")
st.title("🎾 테니스 매치 시스템")

main_mode = st.radio("경기 분류", ["일반 경기", "A팀 vs B팀"], horizontal=True)

# --------- 일반 경기 (단식/복식/혼성 복식) ---------
if main_mode == "일반 경기":
    # 세션 분리
    for k in ["normal_players", "normal_round_matches", "normal_score_record"]:
        if k not in st.session_state:
            st.session_state[k] = [] if "players" in k or "matches" in k else defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
    # 참가자 입력
    with st.expander("1. 참가자 등록", expanded=True):
        with st.form("add_normal_player", clear_on_submit=True):
            name = st.text_input("이름 입력")
            gender = st.radio("성별", ["남", "여"], horizontal=True, key="gN")
            career = st.selectbox("구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년", key="cN")
            submitted = st.form_submit_button("추가")
            if submitted and name:
                st.session_state.normal_players.append({"name": name.strip(), "gender": gender, "career": career})
        if st.session_state.normal_players:
            st.subheader("✅ 현재 참가자 목록")
            for i, p in enumerate(st.session_state.normal_players):
                col1, col2 = st.columns([7, 1])
                col1.markdown(f"- {p['name']} ({p['gender']}, {p['career']}년)")
                if col2.button("❌", key=f"delN_{i}"):
                    st.session_state.normal_players.pop(i)
                    st.rerun()
            st.caption(f"참가자 수: {len(st.session_state.normal_players)}")
            if st.button("🚫 참가자 전체 초기화", key="reset_normal"):
                st.session_state.normal_players.clear()
                st.session_state.normal_round_matches.clear()
                st.session_state.normal_score_record.clear()
                st.rerun()
    # 경기 설정
    match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
    game_per_player = st.number_input("1인당 경기 수 (리그전 전용)", min_value=1, max_value=10, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2, key="normal_courts")
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0), key="normal_time")

    # 구력 기반 매칭 함수
    def get_closest_pairs(player_list):
        players = sorted(player_list, key=lambda p: p['career'])
        pairs = []
        while len(players) >= 2:
            p1 = players.pop(0)
            min_gap = float('inf')
            min_idx = -1
            for i, p2 in enumerate(players):
                gap = abs(p1['career'] - p2['career'])
                if gap < min_gap:
                    min_gap = gap
                    min_idx = i
            p2 = players.pop(min_idx)
            pairs.append((p1, p2))
        return pairs

    def generate_normal_matches(players, match_type):
        if match_type == "혼성 복식":
            males = [p for p in players if p['gender'] == "남"]
            females = [p for p in players if p['gender'] == "여"]
            team_pairs = []
            while males and females:
                m = males.pop(0)
                min_gap = float('inf')
                min_idx = -1
                for i, f in enumerate(females):
                    gap = abs(m['career'] - f['career'])
                    if gap < min_gap:
                        min_gap = gap
                        min_idx = i
                f = females.pop(min_idx)
                team_pairs.append(((m['name'], f['name']), (m['career']+f['career'])/2))
            team_pairs.sort(key=lambda t: t[1])
            matches = []
            teams_only = [tp[0] for tp in team_pairs]
            for i in range(0, len(teams_only) - 1, 2):
                matches.append((teams_only[i], teams_only[i+1]))
            return matches
        if match_type == "복식":
            pairs = get_closest_pairs(players)
            team_pairs = [((p1['name'], p2['name']), (p1['career'] + p2['career'])/2) for p1, p2 in pairs]
            team_pairs.sort(key=lambda t: t[1])
            teams_only = [tp[0] for tp in team_pairs]
            matches = []
            for i in range(0, len(teams_only) - 1, 2):
                matches.append((teams_only[i], teams_only[i+1]))
            return matches
        if match_type == "단식":
            pairs = get_closest_pairs(players)
            matches = []
            for p1, p2 in pairs:
                matches.append(((p1['name'],), (p2['name'],)))
            return matches
        return []

    # 대진표 생성
    if st.button("🎯 대진표 생성", key="normal_generate"):
        if len(st.session_state.normal_players) < 2:
            st.warning("2명 이상 필요합니다.")
        else:
            base_time = datetime.datetime.combine(datetime.date.today(), start_time)
            court_cycle = [i+1 for i in range(num_courts)]
            raw_matches = generate_normal_matches(st.session_state.normal_players, match_type)
            st.session_state.normal_round_matches = []
            for i, match in enumerate(raw_matches):
                court = court_cycle[i % num_courts]
                match_time = base_time + datetime.timedelta(minutes=30*i)
                st.session_state.normal_round_matches.append({
                    "team1": match[0],
                    "team2": match[1],
                    "court": court,
                    "time": match_time.strftime('%H:%M'),
                    "score1": "",
                    "score2": ""
                })
            st.session_state.normal_score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
            st.success("✅ 대진표가 생성되었습니다.")
            st.rerun()
    # 점수 입력 및 결과
    if st.session_state.normal_round_matches:
        with st.expander("3. 대진표 및 점수 입력", expanded=True):
            for idx, match in enumerate(st.session_state.normal_round_matches):
                team1 = match['team1']
                team2 = match['team2']
                t1 = team1 if isinstance(team1, str) else " + ".join(team1)
                t2 = team2 if isinstance(team2, str) else " + ".join(team2)
                st.caption(f"코트 {match['court']} / 시간 {match['time']}")
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
                col1.markdown(f"**{t1}**")
                match['score1'] = col2.text_input(" ", key=f"n_s1_{idx}", label_visibility="collapsed")
                col3.markdown("vs")
                match['score2'] = col4.text_input(" ", key=f"n_s2_{idx}", label_visibility="collapsed")
                col5.markdown(f"**{t2}**")
            if st.button("✅ 점수 반영", key="normal_score"):
                for idx, match in enumerate(st.session_state.normal_round_matches):
                    s1, s2 = match['score1'].strip(), match['score2'].strip()
                    if not s1.isdigit() or not s2.isdigit():
                        continue
                    s1, s2 = int(s1), int(s2)
                    team1 = match['team1'] if isinstance(match['team1'], tuple) else [match['team1']]
                    team2 = match['team2'] if isinstance(match['team2'], tuple) else [match['team2']]
                    for p in team1:
                        st.session_state.normal_score_record[p]['득점'] += s1
                        st.session_state.normal_score_record[p]['실점'] += s2
                    for p in team2:
                        st.session_state.normal_score_record[p]['득점'] += s2
                        st.session_state.normal_score_record[p]['실점'] += s1
                    if s1 > s2:
                        for p in team1:
                            st.session_state.normal_score_record[p]['승'] += 1
                        for p in team2:
                            st.session_state.normal_score_record[p]['패'] += 1
                    elif s2 > s1:
                        for p in team2:
                            st.session_state.normal_score_record[p]['승'] += 1
                        for p in team1:
                            st.session_state.normal_score_record[p]['패'] += 1
                st.success("✅ 점수가 반영되었습니다.")
    # 결과 요약
    if st.session_state.normal_score_record and any(st.session_state.normal_score_record.values()):
        with st.expander("📊 결과 요약 및 종합 MVP", expanded=True):
            stats = []
            for name, r in st.session_state.normal_score_record.items():
                total = r['승'] + r['패']
                rate = f"{r['승']/total*100:.1f}%" if total else "0%"
                stats.append((name, r['승'], r['패'], r['득점'], r['실점'], rate))
            df = pd.DataFrame(stats, columns=["이름", "승", "패", "득점", "실점", "승률"])
            df = df.sort_values(by=["승", "득점"], ascending=[False, False])
            df.index += 1
            st.dataframe(df, use_container_width=True)
            st.bar_chart(df.set_index("이름")["승"])
            st.markdown("### 🏅 MVP Top 3")
            for i, row in df.head(3).iterrows():
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else ""
                st.markdown(f"**{medal} {row['이름']}** - 승 {row['승']}, 승률 {row['승률']}")

# --------- 팀 경기 (A팀 vs B팀) ---------
elif main_mode == "A팀 vs B팀":
    for k in ["teamA", "teamB", "team_round_matches", "team_score_record"]:
        if k not in st.session_state:
            st.session_state[k] = [] if "team" in k or "matches" in k else defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})

    st.subheader("A팀 등록")
    with st.form("add_teamA", clear_on_submit=True):
        nameA = st.text_input("A팀 이름 입력")
        genderA = st.radio("A팀 성별", ["남", "여"], horizontal=True, key="gA")
        careerA = st.selectbox("A팀 구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년", key="cA")
        submitA = st.form_submit_button("A팀 추가")
        if submitA and nameA:
            st.session_state.teamA.append({"name": nameA.strip(), "gender": genderA, "career": careerA})

    st.subheader("B팀 등록")
    with st.form("add_teamB", clear_on_submit=True):
        nameB = st.text_input("B팀 이름 입력")
        genderB = st.radio("B팀 성별", ["남", "여"], horizontal=True, key="gB")
        careerB = st.selectbox("B팀 구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년", key="cB")
        submitB = st.form_submit_button("B팀 추가")
        if submitB and nameB:
            st.session_state.teamB.append({"name": nameB.strip(), "gender": genderB, "career": careerB})

    st.markdown("**A팀:**")
    for i, p in enumerate(st.session_state.teamA):
        col1, col2 = st.columns([7, 1])
        col1.markdown(f"- {p['name']} ({p['gender']}, {p['career']}년)")
        if col2.button("❌", key=f"delA_{i}"):
            st.session_state.teamA.pop(i)
            st.rerun()
    st.markdown("**B팀:**")
    for i, p in enumerate(st.session_state.teamB):
        col1, col2 = st.columns([7, 1])
        col1.markdown(f"- {p['name']} ({p['gender']}, {p['career']}년)")
        if col2.button("❌", key=f"delB_{i}"):
            st.session_state.teamB.pop(i)
            st.rerun()
    st.caption(f"A팀: {len(st.session_state.teamA)}명 / B팀: {len(st.session_state.teamB)}명")
    if st.button("🚫 A팀 전체 초기화"):
        st.session_state.teamA.clear()
        st.rerun()
    if st.button("🚫 B팀 전체 초기화"):
        st.session_state.teamB.clear()
        st.rerun()
    team_num_courts = st.number_input("코트 수", min_value=1, value=2, key="team_courts")
    team_start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0), key="team_time")

    # 대진표 생성
    if st.button("🎯 팀 대진표 생성"):
        a_list = st.session_state.teamA
        b_list = st.session_state.teamB
        n_matches = min(len(a_list), len(b_list))
        if n_matches < 1:
            st.warning("A팀/B팀 모두 1명 이상 필요합니다.")
        else:
            random.shuffle(a_list)
            random.shuffle(b_list)
            matches = []
            for i in range(n_matches):
                matches.append(((a_list[i]['name'],), (b_list[i]['name'],)))
            # 대진표 표로 저장
            base_time = datetime.datetime.combine(datetime.date.today(), team_start_time)
            court_cycle = [i+1 for i in range(team_num_courts)]
            st.session_state.team_round_matches = []
            for i, match in enumerate(matches):
                court = court_cycle[i % team_num_courts]
                match_time = base_time + datetime.timedelta(minutes=30*i)
                st.session_state.team_round_matches.append({
                    "team1": match[0],
                    "team2": match[1],
                    "court": court,
                    "time": match_time.strftime('%H:%M'),
                    "score1": "",
                    "score2": ""
                })
            st.session_state.team_score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
            st.success("✅ 팀 대진표가 생성되었습니다.")
            st.rerun()
    # 점수 입력 및 결과
    if st.session_state.team_round_matches:
        with st.expander("3. 대진표 및 점수 입력", expanded=True):
            for idx, match in enumerate(st.session_state.team_round_matches):
                team1 = match['team1']
                team2 = match['team2']
                t1 = team1 if isinstance(team1, str) else " + ".join(team1)
                t2 = team2 if isinstance(team2, str) else " + ".join(team2)
                st.caption(f"코트 {match['court']} / 시간 {match['time']}")
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
                col1.markdown(f"**{t1}**")
                match['score1'] = col2.text_input(" ", key=f"t_s1_{idx}", label_visibility="collapsed")
                col3.markdown("vs")
                match['score2'] = col4.text_input(" ", key=f"t_s2_{idx}", label_visibility="collapsed")
                col5.markdown(f"**{t2}**")
            if st.button("✅ 점수 반영", key="team_score"):
                for idx, match in enumerate(st.session_state.team_round_matches):
                    s1, s2 = match['score1'].strip(), match['score2'].strip()
                    if not s1.isdigit() or not s2.isdigit():
                        continue
                    s1, s2 = int(s1), int(s2)
                    team1 = match['team1'] if isinstance(match['team1'], tuple) else [match['team1']]
                    team2 = match['team2'] if isinstance(match['team2'], tuple) else [match['team2']]
                    for p in team1:
                        st.session_state.team_score_record[p]['득점'] += s1
                        st.session_state.team_score_record[p]['실점'] += s2
                    for p in team2:
                        st.session_state.team_score_record[p]['득점'] += s2
                        st.session_state.team_score_record[p]['실점'] += s1
                    if s1 > s2:
                        for p in team1:
                            st.session_state.team_score_record[p]['승'] += 1
                        for p in team2:
                            st.session_state.team_score_record[p]['패'] += 1
                    elif s2 > s1:
                        for p in team2:
                            st.session_state.team_score_record[p]['승'] += 1
                        for p in team1:
                            st.session_state.team_score_record[p]['패'] += 1
                st.success("✅ 점수가 반영되었습니다.")
    # 결과 요약
    if st.session_state.team_score_record and any(st.session_state.team_score_record.values()):
        with st.expander("📊 결과 요약 및 종합 MVP", expanded=True):
            stats = []
            for name, r in st.session_state.team_score_record.items():
                total = r['승'] + r['패']
                rate = f"{r['승']/total*100:.1f}%" if total else "0%"
                stats.append((name, r['승'], r['패'], r['득점'], r['실점'], rate))
            df = pd.DataFrame(stats, columns=["이름", "승", "패", "득점", "실점", "승률"])
            df = df.sort_values(by=["승", "득점"], ascending=[False, False])
            df.index += 1
            st.dataframe(df, use_container_width=True)
            st.bar_chart(df.set_index("이름")["승"])
            st.markdown("### 🏅 MVP Top 3")
            for i, row in df.head(3).iterrows():
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else ""
                st.markdown(f"**{medal} {row['이름']}** - 승 {row['승']}, 승률 {row['승률']}")
