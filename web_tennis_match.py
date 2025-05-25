import streamlit as st
import random
import pandas as pd
import datetime
from collections import defaultdict, Counter

st.set_page_config(page_title="🎾 테니스 매칭 시스템", layout="centered")
st.title("🎾 테니스 대진표 생성 시스템")

# ---------- 참가자 등록 ----------
if "players" not in st.session_state:
    st.session_state.players = []
if "match_list" not in st.session_state:
    st.session_state.match_list = []
if "score_record" not in st.session_state:
    st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})

with st.expander("1. 참가자 등록", expanded=True):
    with st.form("add_player", clear_on_submit=True):
        name = st.text_input("이름 입력")
        gender = st.radio("성별", ["남", "여"], horizontal=True)
        career = st.selectbox("구력(년수)", list(range(1, 11)), format_func=lambda x: f"{x}년")
        submitted = st.form_submit_button("추가")
        if submitted and name:
            st.session_state.players.append({"name": name.strip(), "gender": gender, "career": career})
    if st.session_state.players:
        st.subheader("✅ 현재 참가자 목록")
        for i, p in enumerate(st.session_state.players):
            col1, col2 = st.columns([7, 1])
            col1.markdown(f"- {p['name']} ({p['gender']}, {p['career']}년)")
            if col2.button("❌", key=f"del_{i}"):
                st.session_state.players.pop(i)
                st.rerun()
        st.caption(f"참가자 수: {len(st.session_state.players)}")
        if st.button("🚫 참가자 전체 초기화"):
            st.session_state.players.clear()
            st.session_state.match_list.clear()
            st.session_state.score_record.clear()
            st.rerun()

# ---------- 경기 설정 ----------
with st.expander("2. 경기 유형별 세부 설정", expanded=True):
    st.markdown("경기 유형별 경기 수를 각각 입력하세요.")
    num_men_doubles = st.number_input("남자 복식 경기 수", min_value=0, max_value=20, value=2)
    num_women_doubles = st.number_input("여자 복식 경기 수", min_value=0, max_value=20, value=2)
    num_mixed_doubles = st.number_input("혼성 복식 경기 수", min_value=0, max_value=20, value=2)
    num_courts = st.number_input("코트 수", min_value=1, value=2)
    start_time = st.time_input("경기 시작 시간", value=datetime.time(9, 0))

# ---------- 페어링(구력 기반, 페어 중복 제한) ----------
def get_unique_pairs(players):
    # 구력 기반으로, 페어 중복 없이 가능한 모든 페어 구하기
    sorted_players = sorted(players, key=lambda p: p['career'])
    n = len(sorted_players)
    pairs = []
    used = set()
    for i in range(n):
        for j in range(i+1, n):
            pair = tuple(sorted([sorted_players[i]['name'], sorted_players[j]['name']]))
            if pair not in used:
                pairs.append(pair)
                used.add(pair)
    random.shuffle(pairs)
    return pairs

def get_unique_mixed_pairs(males, females):
    # 남1+여1 페어로, 중복 없는 가능한 모든 페어 구하기
    pairs = []
    used = set()
    for m in males:
        for f in females:
            pair = (m['name'], f['name'])
            if pair not in used:
                pairs.append(pair)
                used.add(pair)
    random.shuffle(pairs)
    return pairs

# ---------- 경기 스케줄링 함수 (페어 중복 제한, 3연속 출전 금지) ----------
def schedule_matches_with_strict_constraints(
    men, women, n_men_d, n_women_d, n_mix_d, num_courts, start_time):

    games = []
    court_cycle = [i+1 for i in range(num_courts)]
    base_time = datetime.datetime.combine(datetime.date.today(), start_time)
    match_history = []
    # 1. 남복 페어 목록 만들기
    men_objs = [p for p in st.session_state.players if p['name'] in men]
    men_pairs = get_unique_pairs(men_objs)
    men_pairs_cycle = men_pairs.copy()
    # 2. 여복 페어 목록 만들기
    women_objs = [p for p in st.session_state.players if p['name'] in women]
    women_pairs = get_unique_pairs(women_objs)
    women_pairs_cycle = women_pairs.copy()
    # 3. 혼복 페어 목록 만들기
    mixed_pairs = get_unique_mixed_pairs(men_objs, women_objs)
    mixed_pairs_cycle = mixed_pairs.copy()

    # 4. 각 유형별로 경기 수 만큼 페어 조합
    all_types = (
        [("남자 복식", men_pairs_cycle, men_pairs)] * n_men_d +
        [("여자 복식", women_pairs_cycle, women_pairs)] * n_women_d +
        [("혼성 복식", mixed_pairs_cycle, mixed_pairs)] * n_mix_d
    )
    random.shuffle(all_types)

    # 각 참가자의 "최근 2경기 기록"을 위한 큐
    recent_games = defaultdict(list)  # name -> [경기index...]

    # 5. 경기 생성
    for idx, (gtype, pair_cycle, pair_master) in enumerate(all_types):
        attempt = 0
        max_attempts = 1000
        found = False
        while attempt < max_attempts:
            attempt += 1
            if len(pair_cycle) < 2:
                # 페어가 모자라면 master에서 재충전(중복 페어 허용)
                pair_cycle.extend(pair_master)
                random.shuffle(pair_cycle)
            # 랜덤하게 두 팀 추출
            p1 = pair_cycle.pop()
            p2 = pair_cycle.pop()
            if set(p1) & set(p2):  # 한 팀에 중복 멤버 있으면 skip
                pair_cycle.extend([p1, p2])
                continue
            # 3연속 출전 체크 (이름별로 최근 2경기까지 기록)
            all_players = set(p1) | set(p2)
            all_players.discard("BYE")
            violate = False
            for p in all_players:
                recents = recent_games[p][-2:]
                # 바로 전 2경기에 모두 출전했다면 3연속이 됨
                if len(recents) == 2 and recents[0] == idx-1 and recents[1] == idx-2:
                    violate = True
                    break
            if violate:
                # 해당 페어는 잠시 뒤로
                pair_cycle.extend([p1, p2])
                continue
            # OK, 경기 확정
            games.append((gtype, p1, p2))
            match_history.append((gtype, p1, p2))
            for p in all_players:
                recent_games[p].append(idx)
            found = True
            break
        if not found:
            # 마지막까지 안되면 BYE
            games.append((gtype, ("BYE",), ("BYE",)))

    # 코트, 시간 할당
    match_list = []
    for i, (match_type, team1, team2) in enumerate(games):
        court = court_cycle[i % num_courts]
        match_time = base_time + datetime.timedelta(minutes=30*i)
        match_list.append({
            "match_type": match_type,
            "team1": team1,
            "team2": team2,
            "court": court,
            "time": match_time.strftime('%H:%M'),
            "score1": "",
            "score2": ""
        })
    return match_list

# ---------- 대진표 생성 ----------
if st.button("🎯 유형별 대진표 생성"):
    players = st.session_state.players
    men = [p['name'] for p in players if p['gender'] == "남"]
    women = [p['name'] for p in players if p['gender'] == "여"]
    match_list = schedule_matches_with_strict_constraints(
        men, women,
        num_men_doubles, num_women_doubles, num_mixed_doubles,
        num_courts, start_time
    )
    st.session_state.match_list = match_list
    st.session_state.score_record = defaultdict(lambda: {"승":0, "패":0, "득점":0, "실점":0})
    st.success("✅ 대진표가 생성되었습니다.")
    st.rerun()

# ---------- 대진표 및 점수 입력 ----------
if st.session_state.match_list:
    with st.expander("3. 대진표 및 점수 입력", expanded=True):
        for idx, match in enumerate(st.session_state.match_list):
            t1 = " + ".join(match['team1']) if isinstance(match['team1'], (tuple, list)) else match['team1']
            t2 = " + ".join(match['team2']) if isinstance(match['team2'], (tuple, list)) else match['team2']
            st.caption(f"{match['match_type']} / 코트 {match['court']} / 시간 {match['time']}")
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
            col1.markdown(f"**{t1}**")
            match['score1'] = col2.text_input(" ", key=f"s1_{idx}", label_visibility="collapsed")
            col3.markdown("vs")
            match['score2'] = col4.text_input(" ", key=f"s2_{idx}", label_visibility="collapsed")
            col5.markdown(f"**{t2}**")
        if st.button("✅ 점수 반영"):
            for idx, match in enumerate(st.session_state.match_list):
                s1, s2 = match['score1'].strip(), match['score2'].strip()
                if not s1.isdigit() or not s2.isdigit():
                    continue
                s1, s2 = int(s1), int(s2)
                team1 = match['team1'] if isinstance(match['team1'], (tuple, list)) else [match['team1']]
                team2 = match['team2'] if isinstance(match['team2'], (tuple, list)) else [match['team2']]
                for p in team1:
                    if p != "BYE":
                        st.session_state.score_record[p]['득점'] += s1
                        st.session_state.score_record[p]['실점'] += s2
                for p in team2:
                    if p != "BYE":
                        st.session_state.score_record[p]['득점'] += s2
                        st.session_state.score_record[p]['실점'] += s1
                if s1 > s2:
                    for p in team1:
                        if p != "BYE":
                            st.session_state.score_record[p]['승'] += 1
                    for p in team2:
                        if p != "BYE":
                            st.session_state.score_record[p]['패'] += 1
                elif s2 > s1:
                    for p in team2:
                        if p != "BYE":
                            st.session_state.score_record[p]['승'] += 1
                    for p in team1:
                        if p != "BYE":
                            st.session_state.score_record[p]['패'] += 1
            st.success("✅ 점수가 반영되었습니다.")

# ---------- 결과 요약 ----------
if st.session_state.score_record and any(st.session_state.score_record.values()):
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
