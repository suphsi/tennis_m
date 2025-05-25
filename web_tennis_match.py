import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict

st.set_page_config(page_title="🎾 테니스 토너먼트", layout="centered")
st.title("🎾 테니스 리그/토너먼트 매치 시스템")

main_mode = st.radio("경기 분류", ["일반 경기", "A팀 vs B팀"], horizontal=True)

# ---------- 일반 경기(기존 구조) ----------
if main_mode == "일반 경기":
    for k in ["normal_players", "normal_round_matches", "normal_score_record"]:
        if k not in st.session_state:
            st.session_state[k] = [] if "players" in k or "matches" in k else defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
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
    match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
    game_per_player = st.number_input("1인당 경기 수 (리그전 전용)", min_value=1, max_value=10, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2, key="normal_courts")
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0), key="normal_time")

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

# ---------- A팀 vs B팀 ----------
elif main_mode == "A팀 vs B팀":
    for k in ["teamA", "teamB", "teamA_name", "teamB_name", "team_mode", "team_round_matches", "team_score_record"]:
        if k not in st.session_state:
            st.session_state[k] = "" if "name" in k else [] if "team" in k or "matches" in k else defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})

    st.subheader("A팀/B팀 정보 입력")
    teamA_name = st.text_input("A팀 팀명", st.session_state.teamA_name or "A팀")
    teamB_name = st.text_input("B팀 팀명", st.session_state.teamB_name or "B팀")
    st.session_state.teamA_name = teamA_name
    st.session_state.teamB_name = teamB_name
    team_mode = st.radio("팀 경기 유형", ["복식", "혼성 복식"], horizontal=True, key="team_mode_select")
    st.session_state.team_mode = team_mode

    # A팀 입력
    st.markdown(f"#### {teamA_name} 등록")
    with st.form("add_teamA", clear_on_submit=True):
        nameA = st.text_input(f"{teamA_name} 이름 입력")
        genderA = st.radio(f"{teamA_name} 성별", ["남", "여"], horizontal=True, key="gA")
        careerA = st.selectbox(f"{teamA_name} 구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년", key="cA")
        submitA = st.form_submit_button(f"{teamA_name} 추가")
        if submitA and nameA:
            st.session_state.teamA.append({"name": nameA.strip(), "gender": genderA, "career": careerA})

    # B팀 입력
    st.markdown(f"#### {teamB_name} 등록")
    with st.form("add_teamB", clear_on_submit=True):
        nameB = st.text_input(f"{teamB_name} 이름 입력")
        genderB = st.radio(f"{teamB_name} 성별", ["남", "여"], horizontal=True, key="gB")
        careerB = st.selectbox(f"{teamB_name} 구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년", key="cB")
        submitB = st.form_submit_button(f"{teamB_name} 추가")
        if submitB and nameB:
            st.session_state.teamB.append({"name": nameB.strip(), "gender": genderB, "career": careerB})

    st.markdown(f"**{teamA_name}:**")
    for i, p in enumerate(st.session_state.teamA):
        col1, col2 = st.columns([7, 1])
        col1.markdown(f"- {p['name']} ({p['gender']}, {p['career']}년)")
        if col2.button("❌", key=f"delA_{i}"):
            st.session_state.teamA.pop(i)
            st.rerun()
    st.markdown(f"**{teamB_name}:**")
    for i, p in enumerate(st.session_state.teamB):
        col1, col2 = st.columns([7, 1])
        col1.markdown(f"- {p['name']} ({p['gender']}, {p['career']}년)")
        if col2.button("❌", key=f"delB_{i}"):
            st.session_state.teamB.pop(i)
            st.rerun()
    st.caption(f"{teamA_name}: {len(st.session_state.teamA)}명 / {teamB_name}: {len(st.session_state.teamB)}명")
    if st.button(f"🚫 {teamA_name} 전체 초기화"):
        st.session_state.teamA.clear()
        st.rerun()
    if st.button(f"🚫 {teamB_name} 전체 초기화"):
        st.session_state.teamB.clear()
        st.rerun()
    team_num_courts = st.number_input("코트 수", min_value=1, value=2, key="team_courts")
    team_start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0), key="team_time")

    # ----------- 대진표 생성 함수 -----------
    def create_doubles_pairs(team, mode):
        # mode: "복식" 또는 "혼성 복식"
        if mode == "복식":
            # 구력 최소차 순으로 랜덤 복식 페어
            members = sorted(team, key=lambda p: p['career'])
            pairs = []
            used = [False]*len(members)
            for i in range(len(members)):
                if used[i]: continue
                min_gap, min_j = float('inf'), -1
                for j in range(i+1, len(members)):
                    if used[j]: continue
                    gap = abs(members[i]['career'] - members[j]['career'])
                    if gap < min_gap:
                        min_gap, min_j = gap, j
                if min_j != -1:
                    pairs.append((members[i]['name'], members[min_j]['name']))
                    used[i] = used[min_j] = True
            # 홀수면 마지막 1명 BYE 처리
            if not all(used):
                pairs.append((members[used.index(False)], "BYE"))
            return pairs
        else:  # 혼성 복식
            males = [p for p in team if p['gender'] == "남"]
            females = [p for p in team if p['gender'] == "여"]
            pairs = []
            while males and females:
                m = males.pop(0)
                min_gap, min_idx = float('inf'), -1
                for i, f in enumerate(females):
                    gap = abs(m['career'] - f['career'])
                    if gap < min_gap:
                        min_gap, min_idx = gap, i
                if min_idx != -1:
                    f = females.pop(min_idx)
                    pairs.append((m['name'], f['name']))
            # 남거나 페어링 안된 사람 BYE 처리
            for m in males:
                pairs.append((m['name'], "BYE"))
            for f in females:
                pairs.append((f['name'], "BYE"))
            return pairs

    def generate_team_matches(teamA, teamB, mode):
        pairsA = create_doubles_pairs(teamA, mode)
        pairsB = create_doubles_pairs(teamB, mode)
        n_matches = min(len(pairsA), len(pairsB))
        matches = []
        for i in range(n_matches):
            matches.append((pairsA[i], pairsB[i]))
        # 만약 한 쪽이 인원이 부족해 남는 경우는 BYE 표시
        if len(pairsA) > n_matches:
            for i in range(n_matches, len(pairsA)):
                matches.append((pairsA[i], ("BYE", "BYE")))
        if len(pairsB) > n_matches:
            for i in range(n_matches, len(pairsB)):
                matches.append((("BYE", "BYE"), pairsB[i]))
        return matches

    if st.button("🎯 팀 대진표 생성"):
        a_list = st.session_state.teamA
        b_list = st.session_state.teamB
        mode = st.session_state.team_mode
        matches = generate_team_matches(a_list, b_list, mode)
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
    if st.session_state.team_round_matches:
        with st.expander("3. 대진표 및 점수 입력", expanded=True):
            for idx, match in enumerate(st.session_state.team_round_matches):
                team1 = match['team1']
                team2 = match['team2']
                t1 = team1 if isinstance(team1, str) else " + ".join([str(x) for x in team1])
                t2 = team2 if isinstance(team2, str) else " + ".join([str(x) for x in team2])
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
                        if p != "BYE":
                            st.session_state.team_score_record[p]['득점'] += s1
                            st.session_state.team_score_record[p]['실점'] += s2
                    for p in team2:
                        if p != "BYE":
                            st.session_state.team_score_record[p]['득점'] += s2
                            st.session_state.team_score_record[p]['실점'] += s1
                    if s1 > s2:
                        for p in team1:
                            if p != "BYE":
                                st.session_state.team_score_record[p]['승'] += 1
                        for p in team2:
                            if p != "BYE":
                                st.session_state.team_score_record[p]['패'] += 1
                    elif s2 > s1:
                        for p in team2:
                            if p != "BYE":
                                st.session_state.team_score_record[p]['승'] += 1
                        for p in team1:
                            if p != "BYE":
                                st.session_state.team_score_record[p]['패'] += 1
                st.success("✅ 점수가 반영되었습니다.")
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
