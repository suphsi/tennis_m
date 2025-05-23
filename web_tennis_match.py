import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict, deque
from itertools import combinations

st.set_page_config(page_title="🎾 테니스 토너먼트", layout="centered")
st.title("🎾 테니스 리그/토너먼트 매치 시스템")

# --- 초기 세션값 설정 ---
keys = [
    "players", "matches", "mode", "match_type", "round_matches", "current_round",
    "final_scores", "game_history", "start_time", "score_record"
]
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ["players", "matches", "round_matches", "game_history"] else {}

st.session_state.setdefault("new_players", [])

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

# --- 경기 설정 ---
with st.expander("2. 경기 설정", expanded=True):
    match_type = st.radio("경기 유형", ["단식", "복식", "혼성 복식"], horizontal=True)
    mode = st.radio("진행 방식", ["리그전", "토너먼트"], horizontal=True)
    game_per_player = st.number_input("1인당 경기 수 (리그전 전용)", min_value=1, max_value=10, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2)
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0))

# --- 페어 생성 함수 (복식, 혼성복식 홀수 대응) ---
def make_doubles_pairs(names):
    random.shuffle(names)
    pairs = []
    used = set()
    i = 0
    while i < len(names) - 1:
        pairs.append((names[i], names[i+1]))
        used.add(names[i])
        used.add(names[i+1])
        i += 2
    if i < len(names):
        partner_candidates = list(used) if used else names[:i]
        partner = random.choice(partner_candidates)
        pairs.append((names[i], partner))
    return pairs

def make_mixed_pairs(males, females):
    random.shuffle(males)
    random.shuffle(females)
    pairs = []
    used_m = set()
    used_f = set()
    min_len = min(len(males), len(females))
    for i in range(min_len):
        pairs.append((males[i], females[i]))
        used_m.add(males[i])
        used_f.add(females[i])
    if len(males) > len(females):
        for i in range(len(females), len(males)):
            partner = random.choice(list(used_f) if used_f else females)
            pairs.append((males[i], partner))
    elif len(females) > len(males):
        for i in range(len(males), len(females)):
            partner = random.choice(list(used_m) if used_m else males)
            pairs.append((partner, females[i]))
    return pairs

# --- 연속 출전 금지 매치 스케줄러 ---
def schedule_matches_with_no_consecutive(matches, all_players, team_size, max_repeat=2):
    """
    matches: 전체 가능한 매치 리스트 (튜플의 튜플)
    all_players: 참가자 이름 리스트
    team_size: 단식-1, 복식/혼복-2
    max_repeat: 최대 연속 경기 수-1 (2로 하면 3연속 금지)
    """
    final_schedule = []
    last_played = {name: deque(maxlen=max_repeat) for name in all_players}
    assigned_matches = set()
    attempts = 0
    MAX_ATTEMPTS = 5000
    matches = matches.copy()
    random.shuffle(matches)
    while matches and attempts < MAX_ATTEMPTS:
        for i, match in enumerate(matches):
            # 현재 경기 참가자
            flat_players = []
            if team_size == 1:  # 단식
                flat_players = list(match)
            else:  # 복식/혼복
                flat_players = list(match[0]) + list(match[1])
            # 최근 max_repeat 경기에서 나왔던 사람 있는지 체크
            is_repeat = False
            for p in flat_players:
                if len(last_played[p]) == max_repeat and all(last_played[p][j] == 1 for j in range(max_repeat)):
                    is_repeat = True
                    break
            if not is_repeat and match not in assigned_matches:
                final_schedule.append(match)
                for p in flat_players:
                    # 경기 참여하면 기록: 1, 안나오면 0
                    last_played[p].append(1)
                # 나머지 참가자 기록 갱신
                for p in all_players:
                    if p not in flat_players:
                        last_played[p].append(0)
                assigned_matches.add(match)
                matches.pop(i)
                break
        else:
            # 남은 매치들 모두 반복되는 경우라 더 배정 불가
            break
        attempts += 1
    return final_schedule

# --- 매치 생성 함수 (최적화, 캐시 적용, 연속출전금지) ---
@st.cache_data
def cached_generate_matches(players, match_type, game_per_player, mode):
    names = [p['name'] for p in players]
    random.shuffle(names)
    matches = []

    if match_type == "단식":
        all_pairs = list(combinations(names, 2))
        random.shuffle(all_pairs)
        match_count = len(names) * game_per_player // 2
        base_matches = all_pairs[:match_count*3]  # 여유 있게 후보 생성
        scheduled = schedule_matches_with_no_consecutive(base_matches, names, 1, max_repeat=2)
        matches = scheduled[:match_count]

    elif match_type == "복식":
        # 여러 번 페어 생성해서 후보 확보
        base_matches = []
        for _ in range(20):  # 반복 횟수 조절
            pairs = make_doubles_pairs(names)
            match_combis = list(combinations(pairs, 2))
            base_matches.extend(match_combis)
        # 최대 가능한 매치 수 산정
        match_count = max(1, (len(names) * game_per_player) // 2)
        scheduled = schedule_matches_with_no_consecutive(base_matches, names, 2, max_repeat=2)
        matches = scheduled[:match_count]

    elif match_type == "혼성 복식":
        males = [p['name'] for p in players if p['gender'] == "남"]
        females = [p['name'] for p in players if p['gender'] == "여"]
        all_names = males + females
        base_matches = []
        for _ in range(20):  # 반복 횟수 조절
            pairs = make_mixed_pairs(males, females)
            match_combis = list(combinations(pairs, 2))
            base_matches.extend(match_combis)
        match_count = max(1, (len(all_names) * game_per_player) // 2)
        scheduled = schedule_matches_with_no_consecutive(base_matches, all_names, 2, max_repeat=2)
        matches = scheduled[:match_count]

    return matches

# --- 대진표 생성 ---
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

# --- 대진표 및 점수 입력 ---
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