import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict
from itertools import combinations

st.set_page_config(page_title="🎾 테니스 토너먼트", layout="centered")
st.title("🎾 테니스 리그/토너먼트 매치 시스템")

# --- 쿼리 파라미터 기반 뷰어 모드 감지 ---
params = st.query_params()
viewer_mode = params.get('mode', [None])[0] == 'viewer'

# --- 초기 세션값 설정 ---
keys = [
    "players", "matches", "mode", "match_type", "round_matches", "current_round",
    "final_scores", "game_history", "start_time", "score_record"
]
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ["players", "matches", "round_matches", "game_history"] else {}

st.session_state.setdefault("new_players", [])

# --- 뷰어 모드일 때: 경기결과 + MVP만 노출 ---
if viewer_mode:
    st.header("📊 경기 결과 및 MVP (VIEWER MODE)")
    if st.session_state.round_matches:
        with st.expander("3. 대진표 및 점수 현황", expanded=True):
            for idx, match in enumerate(st.session_state.round_matches):
                team1 = match['team1']
                team2 = match['team2']
                t1 = (
                    team1 if isinstance(team1, str)
                    else " + ".join(team1) if isinstance(team1, (list, tuple))
                    else str(team1)
                )
                t2 = (
                    team2 if isinstance(team2, str)
                    else " + ".join(team2) if isinstance(team2, (list, tuple))
                    else str(team2)
                )
                st.caption(f"코트 {match['court']} / 시간 {match['time']}")
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
                col1.markdown(f"**{t1}**")
                col3.markdown("vs")
                col5.markdown(f"**{t2}**")
                s1 = match['score1'] if match['score1'] else "-"
                s2 = match['score2'] if match['score2'] else "-"
                col2.markdown(f"**{s1}**")
                col4.markdown(f"**{s2}**")
    if st.session_state.score_record:
        with st.expander("📊 결과 요약 및 종합 MVP", expanded=True):
            stats = []
            for name, r in st.session_state.score_record.items():
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
    st.stop()  # 관리자 모드 코드 아래는 실행하지 않음

# --- 관리자 기능 (코드 a 원형) ---
with st.expander("1. 참가자 등록", expanded=True):
    with st.form("add_player", clear_on_submit=True):
        name = st.text_input("이름 입력")
        gender = st.radio("성별", ["남", "여"], horizontal=True)
        submitted = st.form_submit_button("추가")
        if submitted and name:
            st.session_state.new_players.append({"name": name.strip(), "gender": gender})

    if st.session_state.new_players:
        st.subheader("✅ 현재 참가자 목록")
        for idx, p in enumerate(st.session_state.new_players):
            cols = st.columns([8, 1])
            cols[0].markdown(f"- {p['name']} ({p['gender']})")
            if cols[1].button("❌", key=f"del_{idx}"):
                st.session_state.new_players.pop(idx)
                st.rerun()
        st.markdown(f"**현재 참가자 수: {len(st.session_state.new_players)}명**")
        col1, col2 = st.columns(2)
        if col1.button("⏪ 직전 참가자 취소"):
            if st.session_state.new_players:
                st.session_state.new_players.pop()
                st.rerun()
        if col2.button("🚫 참가자 전체 초기화"):
            st.session_state.new_players.clear()
            st.session_state.players.clear()
            st.session_state.round_matches.clear()
            st.session_state.score_record.clear()
            st.session_state.game_history.clear()
            st.rerun()

with st.expander("2. 경기 설정", expanded=True):
    match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
    mode = st.radio("진행 방식", ["리그전", "토너먼트"], horizontal=True)
    game_per_player = st.number_input("1인당 경기 수 (리그전 전용)", min_value=1, max_value=10, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2)
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0))

# --- 복식, 혼성복식 고유 파트너 매치 생성 ---
def generate_unique_doubles_matches(names, game_per_player):
    all_possible_pairs = set()
    n = len(names)
    for i in range(n):
        for j in range(i+1, n):
            all_possible_pairs.add(tuple(sorted([names[i], names[j]])))
    used_teams = set()
    all_matches = []
    attempts = 0
    max_attempts = 2000
    while len(all_matches) < (n * game_per_player) // 2 and attempts < max_attempts:
        teams = []
        available = list(all_possible_pairs - used_teams)
        random.shuffle(available)
        used_in_round = set()
        i = 0
        while i < len(available):
            team = available[i]
            if any(p in used_in_round for p in team):
                i += 1
                continue
            teams.append(team)
            used_in_round.update(team)
            used_teams.add(team)
            i += 1
        # 한 라운드 팀으로 매치 생성 (팀끼리 멤버 중복 없는 매치)
        for i in range(0, len(teams) - 1, 2):
            t1, t2 = teams[i], teams[i+1]
            if set(t1).isdisjoint(set(t2)):
                all_matches.append((t1, t2))
        attempts += 1
        if len(available) < 4:  # 더 이상 팀 조합이 불가
            break
    return all_matches

def generate_unique_mixed_doubles_matches(males, females, game_per_player):
    all_possible_pairs = set()
    for m in males:
        for f in females:
            all_possible_pairs.add((m, f))
    used_teams = set()
    all_matches = []
    total_players = len(males) + len(females)
    attempts = 0
    max_attempts = 2000
    while len(all_matches) < (total_players * game_per_player) // 2 and attempts < max_attempts:
        teams = []
        available = list(all_possible_pairs - used_teams)
        random.shuffle(available)
        used_in_round = set()
        i = 0
        while i < len(available):
            team = available[i]
            if any(p in used_in_round for p in team):
                i += 1
                continue
            teams.append(team)
            used_in_round.update(team)
            used_teams.add(team)
            i += 1
        # 매치 생성 (팀 멤버 중복 없이)
        for i in range(0, len(teams) - 1, 2):
            t1, t2 = teams[i], teams[i+1]
            if set(t1).isdisjoint(set(t2)):
                all_matches.append((t1, t2))
        attempts += 1
        if len(available) < 4:
            break
    return all_matches

@st.cache_data
def cached_generate_matches(players, match_type, game_per_player, mode):
    names = [p['name'] for p in players]
    random.shuffle(names)
    matches = []

    if match_type == "단식":
        all_pairs = list(combinations(names, 2))
        random.shuffle(all_pairs)
        match_count = len(names) * game_per_player // 2
        matches = all_pairs[:match_count]

    elif match_type == "복식":
        matches = generate_unique_doubles_matches(names, game_per_player)

    elif match_type == "혼성 복식":
        males = [p['name'] for p in players if p['gender'] == "남"]
        females = [p['name'] for p in players if p['gender'] == "여"]
        matches = generate_unique_mixed_doubles_matches(males, females, game_per_player)

    return matches

if st.button("🎯 대진표 생성"):
    if len(st.session_state.new_players) < 2:
        st.warning("2명 이상 필요합니다.")
    else:
        st.session_state.players = st.session_state.new_players.copy()
        base_time = datetime.datetime.combine(datetime.date.today(), start_time)
        court_cycle = [i + 1 for i in range(num_courts)]
        raw_matches = cached_generate_matches(
            st.session_state.players, match_type, game_per_player, mode)
        if not raw_matches:
            st.error("대진표를 생성할 수 없습니다.")
        else:
            st.session_state.round_matches = []
            for i, match in enumerate(raw_matches):
                court = court_cycle[i % num_courts]
                match_time = base_time + datetime.timedelta(minutes=30 * i)
                st.session_state.round_matches.append({
                    "team1": match[0],
                    "team2": match[1],
                    "court": court,
                    "time": match_time.strftime('%H:%M'),
                    "score1": "",
                    "score2": ""
                })
            st.session_state.score_record = defaultdict(lambda: {"승": 0, "패": 0, "득점": 0, "실점": 0})
            st.session_state.game_history.clear()
            st.success("✅ 대진표가 생성되었습니다.")
            st.rerun()

if st.session_state.round_matches:
    with st.expander("3. 대진표 및 점수 입력", expanded=True):
        for idx, match in enumerate(st.session_state.round_matches):
            team1 = match['team1']
            team2 = match['team2']
            t1 = (
                team1 if isinstance(team1, str)
                else " + ".join(team1) if isinstance(team1, (list, tuple))
                else str(team1)
            )
            t2 = (
                team2 if isinstance(team2, str)
                else " + ".join(team2) if isinstance(team2, (list, tuple))
                else str(team2)
            )
            st.caption(f"코트 {match['court']} / 시간 {match['time']}")
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
            col1.markdown(f"**{t1}**")
            match['score1'] = col2.text_input(" ", key=f"s1_{idx}", label_visibility="collapsed")
            col3.markdown("vs")
            match['score2'] = col4.text_input(" ", key=f"s2_{idx}", label_visibility="collapsed")
            col5.markdown(f"**{t2}**")

        if st.button("✅ 점수 반영"):
            for idx, match in enumerate(st.session_state.round_matches):
                s1, s2 = match['score1'].strip(), match['score2'].strip()
                if not s1.isdigit() or not s2.isdigit():
                    continue
                s1, s2 = int(s1), int(s2)
                team1 = match['team1'] if isinstance(match['team1'], tuple) else [match['team1']]
                team2 = match['team2'] if isinstance(match['team2'], tuple) else [match['team2']]
                for p in team1:
                    st.session_state.score_record[p]['득점'] += s1
                    st.session_state.score_record[p]['실점'] += s2
                for p in team2:
                    st.session_state.score_record[p]['득점'] += s2
                    st.session_state.score_record[p]['실점'] += s1
                if s1 > s2:
                    for p in team1:
                        st.session_state.score_record[p]['승'] += 1
                    for p in team2:
                        st.session_state.score_record[p]['패'] += 1
                elif s2 > s1:
                    for p in team2:
                        st.session_state.score_record[p]['승'] += 1
                    for p in team1:
                        st.session_state.score_record[p]['패'] += 1
            st.success("✅ 점수가 반영되었습니다.")

if st.session_state.score_record:
    with st.expander("📊 결과 요약 및 종합 MVP", expanded=True):
        stats = []
        for name, r in st.session_state.score_record.items():
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
