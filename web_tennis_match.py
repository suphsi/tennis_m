import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict
from itertools import combinations

st.set_page_config(page_title="🎾 테니스 토너먼트", layout="centered")

params = st.query_params  # 최신 쿼리파라미터 방식

# --- 초기 세션값 설정 ---
keys = ["players", "matches", "mode", "match_type", "round_matches", "current_round", "final_scores", "game_history", "start_time", "score_record"]
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ["players", "matches", "round_matches", "game_history"] else {}

st.session_state.setdefault("new_players", [])

# --- 복식/혼성복식 팀 조합 조건 함수 ---
def generate_doubles_matches(players, game_per_player, is_mixed=False):
    matches = []
    partner_counts = defaultdict(lambda: defaultdict(int))
    all_players = [p['name'] for p in players]

    if is_mixed:
        males = [p['name'] for p in players if p['gender'] == '남']
        females = [p['name'] for p in players if p['gender'] == '여']
        min_pairs = min(len(males), len(females))
        for round_no in range(game_per_player):
            random.shuffle(males)
            random.shuffle(females)
            round_teams = []
            used_males, used_females = set(), set()
            for m, f in zip(males, females):
                # 파트너 2회 이상 금지
                if partner_counts[m][f] >= 2 or partner_counts[f][m] >= 2:
                    continue
                round_teams.append((m, f))
                partner_counts[m][f] += 1
                partner_counts[f][m] += 1
                used_males.add(m)
                used_females.add(f)
            round_pool = round_teams[:]
            random.shuffle(round_pool)
            for i in range(0, len(round_pool) - 1, 2):
                t1 = round_pool[i]
                t2 = round_pool[i+1]
                # 한 경기 내 팀 중복 멤버 방지
                if set(t1) & set(t2):
                    continue
                matches.append((t1, t2))
    else:
        # 복식
        for round_no in range(game_per_player):
            available = all_players[:]
            random.shuffle(available)
            round_teams = []
            while len(available) >= 2:
                a = available.pop()
                b = available.pop()
                if partner_counts[a][b] >= 2 or partner_counts[b][a] >= 2:
                    continue
                round_teams.append((a, b))
                partner_counts[a][b] += 1
                partner_counts[b][a] += 1
            random.shuffle(round_teams)
            for i in range(0, len(round_teams) - 1, 2):
                t1 = round_teams[i]
                t2 = round_teams[i+1]
                if set(t1) & set(t2):
                    continue
                matches.append((t1, t2))
    return matches

def generate_matches(players, match_type, game_per_player):
    if match_type == "혼성 복식":
        return generate_doubles_matches(players, game_per_player, is_mixed=True)
    elif match_type == "복식":
        return generate_doubles_matches(players, game_per_player, is_mixed=False)
    elif match_type == "단식":
        names = [p['name'] for p in players]
        random.shuffle(names)
        matches = []
        for i in range(0, len(names) - 1, 2):
            matches.append(((names[i],), (names[i+1],)))
        return matches
    return []

# --- 뷰어 모드 (mode=viewer) ---
if "mode" in params and params["mode"][0] == "viewer":
    st.title("🎾 경기 결과 뷰어")
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
    else:
        st.info("아직 기록된 경기 결과가 없습니다.")
    st.stop()

# --- 일반 모드 (관리자/운영자용) ---
st.title("🎾 테니스 리그/토너먼트 매치 시스템")

# --- 참가자 입력 ---
with st.expander("1. 참가자 등록", expanded=True):
    with st.form("add_player", clear_on_submit=True):
        name = st.text_input("이름 입력")
        gender = st.radio("성별", ["남", "여"], horizontal=True)
        submitted = st.form_submit_button("추가")
        if submitted and name:
            st.session_state.new_players.append({"name": name.strip(), "gender": gender})

    if st.session_state.new_players:
        st.subheader("✅ 현재 참가자 목록")
        for i, p in enumerate(st.session_state.new_players):
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"- {p['name']} ({p['gender']})")
            if col2.button("❌", key=f"del_{i}"):
                st.session_state.new_players.pop(i)
                st.rerun()
        st.caption(f"참가자 수: {len(st.session_state.new_players)}")

        if st.button("🚫 참가자 전체 초기화"):
            st.session_state.new_players.clear()
            st.session_state.players.clear()
            st.session_state.round_matches.clear()
            st.session_state.score_record.clear()
            st.session_state.game_history.clear()
            st.rerun()

# --- 설정 ---
with st.expander("2. 경기 설정", expanded=True):
    match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
    mode = st.radio("진행 방식", ["리그전", "토너먼트"], horizontal=True)
    game_per_player = st.number_input("1인당 경기 수 (리그전 전용)", min_value=1, max_value=10, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2)
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0))

# --- 대진표 생성 ---
if st.button("🎯 대진표 생성"):
    if len(st.session_state.new_players) < 2:
        st.warning("2명 이상 필요합니다.")
    else:
        st.session_state.players = st.session_state.new_players.copy()
        base_time = datetime.datetime.combine(datetime.date.today(), start_time)
        court_cycle = [i+1 for i in range(num_courts)]
        raw_matches = generate_matches(st.session_state.players, match_type, game_per_player)
        st.session_state.round_matches = []
        for i, match in enumerate(raw_matches):
            court = court_cycle[i % num_courts]
            match_time = base_time + datetime.timedelta(minutes=30*i)
            st.session_state.round_matches.append({
                "team1": match[0],
                "team2": match[1],
                "court": court,
                "time": match_time.strftime('%H:%M'),
                "score1": "",
                "score2": ""
            })
        st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
        st.session_state.game_history.clear()
        st.success("✅ 대진표가 생성되었습니다.")
        st.rerun()

# --- 대진표 + 점수 입력 ---
if st.session_state.round_matches:
    with st.expander("3. 대진표 및 점수 입력", expanded=True):
        for idx, match in enumerate(st.session_state.round_matches):
            team1 = match['team1']
            team2 = match['team2']
            t1 = team1 if isinstance(team1, str) else " + ".join(team1)
            t2 = team2 if isinstance(team2, str) else " + ".join(team2)
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

# --- 결과 요약 ---
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
