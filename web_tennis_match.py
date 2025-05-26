import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict
from itertools import combinations

st.set_page_config(page_title="🎾 테니스 토너먼트", layout="centered")
st.title("🎾 테니스 리그/토너먼트 매치 시스템")

# --- 상태 초기화 ---
def init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

init_state("main_mode", "일반 경기")
init_state("normal_players", [])
init_state("normal_round_matches", [])
init_state("normal_score_record", defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0}))
init_state("teamA", [])
init_state("teamB", [])
init_state("teamA_name", "A팀")
init_state("teamB_name", "B팀")
init_state("team_mode", "복식")
init_state("team_round_matches", [])
init_state("team_score_record", defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0}))

main_mode = st.radio("경기 분류", ["일반 경기", "A팀 vs B팀"], horizontal=True, key="main_mode")

# ----------------- 공통 함수 -----------------
def get_pairs_by_career(player_list, n_pairs=None, match_type="복식"):
    """구력 기준 페어링 (복식/혼복/단식)"""
    players = sorted(player_list, key=lambda p: p['career'])
    if match_type == "혼성 복식":
        males = [p for p in players if p['gender'] == "남"]
        females = [p for p in players if p['gender'] == "여"]
        pairs = []
        while males and females:
            m = males.pop(0)
            f = min(females, key=lambda x: abs(x['career'] - m['career']))
            females.remove(f)
            pairs.append(((m['name'], f['name']), (m['career']+f['career'])/2))
        # 홀수면 남은 사람 BYE
        for m in males:
            pairs.append(((m['name'], "BYE"), m['career']))
        for f in females:
            pairs.append((("BYE", f['name']), f['career']))
    else:  # 복식/단식
        pairs = []
        pl = players.copy()
        while len(pl) >= 2:
            p1 = pl.pop(0)
            p2 = min(pl, key=lambda x: abs(x['career'] - p1['career']))
            pl.remove(p2)
            pairs.append(((p1['name'], p2['name']), (p1['career'] + p2['career'])/2))
        # 홀수면 BYE
        if pl:
            pairs.append(((pl[0]['name'], "BYE"), pl[0]['career']))
    # 페어 중간값으로 정렬 (비슷한 구력끼리 붙게)
    pairs.sort(key=lambda t: t[1])
    return [tp[0] for tp in pairs[:n_pairs]] if n_pairs else [tp[0] for tp in pairs]

def assign_matches_evenly(team_pairs, num_matches):
    """모든 페어가 최대한 균등하게 매치 횟수 배정"""
    matches = []
    cnt = 0
    num_pairs = len(team_pairs)
    for i in range(num_matches):
        idx1, idx2 = i % num_pairs, (i+1) % num_pairs
        if idx1 != idx2:
            matches.append((team_pairs[idx1], team_pairs[idx2]))
        else:
            # 불가피하게 자기자신이면 BYE
            matches.append((team_pairs[idx1], ("BYE", "BYE")))
        cnt += 1
    return matches

def schedule_matches(match_settings, players):
    """경기 유형/횟수별로 균등 배정된 대진표 생성"""
    matches = []
    base_time = datetime.datetime.combine(datetime.date.today(), match_settings["start_time"])
    court_cycle = [i+1 for i in range(match_settings["num_courts"])]
    m_idx = 0
    for mtype, n_games in match_settings["game_counts"].items():
        if n_games <= 0:
            continue
        if mtype == "남자 복식":
            group = [p for p in players if p['gender'] == "남"]
        elif mtype == "여자 복식":
            group = [p for p in players if p['gender'] == "여"]
        elif mtype == "혼성 복식":
            group = players
        else:
            continue
        pairs = get_pairs_by_career(group, n_pairs=None, match_type="혼성 복식" if mtype=="혼성 복식" else "복식")
        # 필요한 페어 수만큼만 추출(부족하면 BYE)
        num_pairs = max(2, min(len(pairs), n_games+1))
        pairs = pairs[:num_pairs]
        mt = assign_matches_evenly(pairs, n_games)
        for i, (team1, team2) in enumerate(mt):
            court = court_cycle[m_idx % len(court_cycle)]
            match_time = base_time + datetime.timedelta(minutes=30*m_idx)
            matches.append({
                "match_type": mtype,
                "team1": team1,
                "team2": team2,
                "court": court,
                "time": match_time.strftime('%H:%M'),
                "score1": "",
                "score2": ""
            })
            m_idx += 1
    return matches

def handle_score_input(round_matches, score_record, score_prefix=""):
    for idx, match in enumerate(round_matches):
        s1, s2 = match['score1'].strip(), match['score2'].strip()
        if not s1.isdigit() or not s2.isdigit():
            continue
        s1, s2 = int(s1), int(s2)
        team1 = match['team1'] if isinstance(match['team1'], tuple) else [match['team1']]
        team2 = match['team2'] if isinstance(match['team2'], tuple) else [match['team2']]
        for p in team1:
            if p != "BYE":
                score_record[p]['득점'] += s1
                score_record[p]['실점'] += s2
        for p in team2:
            if p != "BYE":
                score_record[p]['득점'] += s2
                score_record[p]['실점'] += s1
        if s1 > s2:
            for p in team1:
                if p != "BYE":
                    score_record[p]['승'] += 1
            for p in team2:
                if p != "BYE":
                    score_record[p]['패'] += 1
        elif s2 > s1:
            for p in team2:
                if p != "BYE":
                    score_record[p]['승'] += 1
            for p in team1:
                if p != "BYE":
                    score_record[p]['패'] += 1
    return score_record

def result_summary(score_record, key=""):
    if not score_record or not any(score_record.values()):
        return
    with st.expander("📊 결과 요약 및 종합 MVP", expanded=True):
        stats = []
        for name, r in score_record.items():
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

# --------- 일반 경기 모드 ---------
if main_mode == "일반 경기":
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

    st.markdown("경기 유형별 경기 수를 입력하세요.")
    n_men_d = st.number_input("남자 복식 경기 수", min_value=0, max_value=20, value=2)
    n_women_d = st.number_input("여자 복식 경기 수", min_value=0, max_value=20, value=2)
    n_mixed_d = st.number_input("혼성 복식 경기 수", min_value=0, max_value=20, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2, key="normal_courts")
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0), key="normal_time")
    match_settings = {
        "game_counts": {
            "남자 복식": n_men_d,
            "여자 복식": n_women_d,
            "혼성 복식": n_mixed_d
        },
        "num_courts": num_courts,
        "start_time": start_time
    }

    if st.button("🎯 대진표 생성", key="normal_generate"):
        if len(st.session_state.normal_players) < 2:
            st.warning("2명 이상 필요합니다.")
        else:
            matches = schedule_matches(match_settings, st.session_state.normal_players)
            st.session_state.normal_round_matches = matches
            st.session_state.normal_score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
            st.success("✅ 대진표가 생성되었습니다.")
            st.rerun()

    if st.session_state.normal_round_matches:
        with st.expander("3. 대진표 및 점수 입력", expanded=True):
            for idx, match in enumerate(st.session_state.normal_round_matches):
                t1 = " + ".join(match['team1']) if isinstance(match['team1'], (tuple, list)) else match['team1']
                t2 = " + ".join(match['team2']) if isinstance(match['team2'], (tuple, list)) else match['team2']
                st.caption(f"{match['match_type']} / 코트 {match['court']} / 시간 {match['time']}")
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
                col1.markdown(f"**{t1}**")
                match['score1'] = col2.text_input(" ", key=f"n_s1_{idx}", label_visibility="collapsed")
                col3.markdown("vs")
                match['score2'] = col4.text_input(" ", key=f"n_s2_{idx}", label_visibility="collapsed")
                col5.markdown(f"**{t2}**")
            if st.button("✅ 점수 반영", key="normal_score"):
                handle_score_input(st.session_state.normal_round_matches, st.session_state.normal_score_record)
                st.success("✅ 점수가 반영되었습니다.")

    result_summary(st.session_state.normal_score_record, key="normal")

# --------- A팀 vs B팀 ---------
elif main_mode == "A팀 vs B팀":
    st.subheader("A팀/B팀 정보 입력")
    teamA_name = st.text_input("A팀 팀명", st.session_state.teamA_name)
    teamB_name = st.text_input("B팀 팀명", st.session_state.teamB_name)
    st.session_state.teamA_name = teamA_name
    st.session_state.teamB_name = teamB_name
    team_mode = st.radio("팀 경기 유형", ["복식", "혼성 복식"], horizontal=True, key="team_mode_select")
    st.session_state.team_mode = team_mode

    st.markdown(f"#### {teamA_name} 등록")
    with st.form("add_teamA", clear_on_submit=True):
        nameA = st.text_input(f"{teamA_name} 이름 입력")
        genderA = st.radio(f"{teamA_name} 성별", ["남", "여"], horizontal=True, key="gA")
        careerA = st.selectbox(f"{teamA_name} 구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년", key="cA")
        submitA = st.form_submit_button(f"{teamA_name} 추가")
        if submitA and nameA:
            st.session_state.teamA.append({"name": nameA.strip(), "gender": genderA, "career": careerA})

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

    st.markdown("경기 유형별 경기 수를 입력하세요.")
    n_men_d = st.number_input("남자 복식 경기 수", min_value=0, max_value=20, value=2, key="team_men_d")
    n_women_d = st.number_input("여자 복식 경기 수", min_value=0, max_value=20, value=2, key="team_women_d")
    n_mixed_d = st.number_input("혼성 복식 경기 수", min_value=0, max_value=20, value=2, key="team_mixed_d")
    team_num_courts = st.number_input("코트 수", min_value=1, value=2, key="team_courts")
    team_start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0), key="team_time")
    match_settings = {
        "game_counts": {
            "남자 복식": n_men_d,
            "여자 복식": n_women_d,
            "혼성 복식": n_mixed_d
        },
        "num_courts": team_num_courts,
        "start_time": team_start_time
    }

    if st.button("🎯 팀 대진표 생성"):
        all_players = st.session_state.teamA + st.session_state.teamB
        matches = schedule_matches(match_settings, all_players)
        st.session_state.team_round_matches = matches
        st.session_state.team_score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
        st.success("✅ 팀 대진표가 생성되었습니다.")
        st.rerun()

    if st.session_state.team_round_matches:
        with st.expander("3. 대진표 및 점수 입력", expanded=True):
            for idx, match in enumerate(st.session_state.team_round_matches):
                t1 = " + ".join(match['team1']) if isinstance(match['team1'], (tuple, list)) else match['team1']
                t2 = " + ".join(match['team2']) if isinstance(match['team2'], (tuple, list)) else match['team2']
                st.caption(f"{match['match_type']} / 코트 {match['court']} / 시간 {match['time']}")
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
                col1.markdown(f"**{t1}**")
                match['score1'] = col2.text_input(" ", key=f"t_s1_{idx}", label_visibility="collapsed")
                col3.markdown("vs")
                match['score2'] = col4.text_input(" ", key=f"t_s2_{idx}", label_visibility="collapsed")
                col5.markdown(f"**{t2}**")
            if st.button("✅ 점수 반영", key="team_score"):
                handle_score_input(st.session_state.team_round_matches, st.session_state.team_score_record)
                st.success("✅ 점수가 반영되었습니다.")

    result_summary(st.session_state.team_score_record, key="team")
