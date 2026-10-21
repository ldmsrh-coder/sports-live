#!/usr/bin/env python3
"""Collect current-month Korean sports schedules into a static JSON snapshot.

The site remains static-hosted. This scheduled collector removes browser CORS
as a single point of failure and keeps the previous snapshot if all providers
fail or an unexpectedly empty response arrives.
"""
from __future__ import annotations

import calendar
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "korean-sports.json"
KST = ZoneInfo("Asia/Seoul")
TIMEOUT = 18
HEADERS = {
    "User-Agent": "sports-live-korean-sports-collector/1.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

TEAM_MAP = {
    "KIA": "KIA 타이거즈", "KIA Tigers": "KIA 타이거즈",
    "LG": "LG 트윈스", "LG Twins": "LG 트윈스",
    "두산": "두산 베어스", "Doosan Bears": "두산 베어스",
    "KT": "KT 위즈", "KT Wiz": "KT 위즈",
    "SSG": "SSG 랜더스", "SSG Landers": "SSG 랜더스",
    "롯데": "롯데 자이언츠", "Lotte Giants": "롯데 자이언츠",
    "한화": "한화 이글스", "Hanwha Eagles": "한화 이글스",
    "삼성": "삼성 라이온즈", "Samsung Lions": "삼성 라이온즈",
    "NC": "NC 다이노스", "NC Dinos": "NC 다이노스",
    "키움": "키움 히어로즈", "Kiwoom Heroes": "키움 히어로즈",
    "현대건설": "현대건설 힐스테이트", "GS칼텍스": "GS칼텍스 서울 KIXX",
    "흥국생명": "흥국생명 핑크스파이더스", "도로공사": "한국도로공사 하이패스",
    "한국도로공사": "한국도로공사 하이패스", "정관장": "정관장 레드스파크스",
    "삼성화재": "삼성화재 블루팡스", "한국전력": "한국전력 빅스톰",
    "현대캐피탈": "현대캐피탈 스카이워커스", "대한항공": "대한항공 점보스",
    "우리카드": "우리카드 우리WON", "KB손해보험": "KB손해보험 스타즈",
    "OK저축은행": "OK저축은행 읏맨", "페퍼저축은행": "페퍼저축은행 AI페퍼스",
    "KB스타즈": "KB스타즈", "삼성생명": "삼성생명 블루밍스",
    "우리은행": "우리은행 우리WON", "신한은행": "신한은행 에스버드",
    "하나은행": "하나은행", "BNK 썸": "BNK 썸",
}
STATUS_MAP = {
    "FE": "종료", "FINAL": "종료", "FINISHED": "종료", "F": "종료",
    "NS": "예정", "SCHEDULED": "예정", "PREVIEW": "예정",
    "LIVE": "진행 중", "IN": "진행 중", "IN PROGRESS": "진행 중",
    "HT": "하프타임", "PP": "연기", "POSTPONED": "연기",
    "CAN": "취소", "CANCELLED": "취소", "CANCELED": "취소",
    "SUSP": "중단", "SUSPENDED": "중단",
}

def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()

def team(value) -> str:
    value = clean(value)
    return TEAM_MAP.get(value, value)

def status(value, fallback="예정") -> str:
    value = clean(value)
    upper = value.upper()
    if upper in STATUS_MAP:
        return STATUS_MAP[upper]
    if any(x in value for x in ("우천취소", "경기취소", "취소")):
        return "취소"
    if any(x in value for x in ("연기", "순연")):
        return "연기"
    if any(x in value for x in ("경기중", "진행 중", "진행중", "LIVE")):
        return "진행 중"
    if any(x in value for x in ("경기종료", "종료")):
        return "종료"
    if value in ("하프타임", "승부차기", "연장전 진행 중") or re.search(r"^[1-4]쿼터 (진행 중|종료)$", value):
        return value
    return fallback

def make_game(date, time, home, away, hs="-", away_score="-", league="", sport="", source="", state="예정", game_id=""):
    date = clean(date)[:10].replace("/", "-").replace(".", "-")
    time = clean(time)
    if re.fullmatch(r"\d{4}", time):
        time = time[:2] + ":" + time[2:]
    if not re.fullmatch(r"\d{2}:\d{2}", time):
        time = ""
    home, away = team(home), team(away)
    if not date or not home or not away:
        return None
    return {
        "id": clean(game_id),
        "date": date,
        "time": time or "시간 미정",
        "home": home,
        "away": away,
        "homeScore": str(hs) if hs is not None and str(hs) != "" else "-",
        "awayScore": str(away_score) if away_score is not None and str(away_score) != "" else "-",
        "status": status(state),
        "league": league,
        "sport": sport,
        "source": source,
        "rawTime": f"{date}T{time}:00+09:00" if time else date,
    }

def parse_date(value, year, month):
    match = re.search(r"(?:(\d{4})[./-])?(\d{1,2})[./-](\d{1,2})", clean(value))
    if not match:
        return None
    y = int(match.group(1) or year)
    m, d = int(match.group(2)), int(match.group(3))
    try:
        parsed = datetime(y, m, d)
    except ValueError:
        return None
    if parsed.year != year or parsed.month != month:
        return None
    return parsed.strftime("%Y-%m-%d")

def month_bounds(year, month):
    first = f"{year:04d}{month:02d}01"
    last = f"{year:04d}{month:02d}{calendar.monthrange(year, month)[1]:02d}"
    return first, last

def unpack_array(payload, keys=("data", "result", "list", "matches", "fixtures", "scheduleList")):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = unpack_array(value, keys)
            if nested:
                return nested
    for value in payload.values():
        if isinstance(value, list):
            return value
    return []

def fetch_kleague(year, month):
    out = []
    url = "https://www.kleague.com/getScheduleList.do"
    for league_id in (1, 2):
        response = SESSION.post(url, json={"year": str(year), "month": f"{month:02d}", "leagueId": league_id}, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        items = data.get("scheduleList", []) if isinstance(data, dict) else []
        for item in items:
            day = parse_date(item.get("gameDate"), year, month)
            if not day:
                continue
            code = clean(item.get("gameStatus") or ("FE" if item.get("endYn") == "Y" else "NS"))
            game = make_game(
                day, item.get("gameTime"), item.get("homeTeamName") or item.get("homeTeam"),
                item.get("awayTeamName") or item.get("awayTeam"), item.get("homeGoal", "-"),
                item.get("awayGoal", "-"), f"대한민국 K리그 {league_id}부", "football",
                "K리그 공식 일정", code, item.get("gameId"),
            )
            if game:
                out.append(game)
    return out

def fetch_kbl(year, month):
    start, end = month_bounds(year, month)
    season_end_year = year + 1 if month >= 10 else year
    url = f"https://api.kbl.or.kr/match/list?season={season_end_year}"
    response = SESSION.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    out = []
    for item in unpack_array(payload):
        raw_date = clean(item.get("game_date") or item.get("gameDate") or item.get("date"))
        if re.fullmatch(r"\d{8}", raw_date):
            day = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        else:
            day = parse_date(raw_date, year, month)
        if not day or not day.startswith(f"{year:04d}-{month:02d}"):
            continue
        start_time = clean(item.get("game_start") or item.get("gameStart") or item.get("game_time") or "")
        started, ended = str(item.get("is_started", "0")) == "1", str(item.get("is_ended", "0")) == "1"
        quarter = clean(item.get("playing_quarter"))
        game_status = "종료" if ended else (f"{quarter} 진행 중" if started and quarter and quarter != "X" else ("진행 중" if started else "예정"))
        game = make_game(
            day, start_time, item.get("home_team_name_full") or item.get("home_team_name"),
            item.get("away_team_name_full") or item.get("away_team_name"),
            item.get("home_score", "-"), item.get("away_score", "-"),
            "대한민국 KBL 프로농구", "basketball", "KBL 공식 API", game_status, item.get("gmkey"),
        )
        if game:
            out.append(game)
    return out

def fetch_kovo(year, month):
    season_year = year if month >= 10 else year - 1
    season_code = f"{season_year - 2003:03d}"
    out = []
    for round_no in range(1, 7):
        url = f"https://user-api.kovo.co.kr/stat/game-schedule?gcode=001&seasonCode={season_code}&leagueCode=201&round={round_no}"
        response = SESSION.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("payload", {}).get("content", []) if isinstance(payload, dict) else []
        for item in items if isinstance(items, list) else []:
            day = parse_date(item.get("gdate") or item.get("gameDate") or item.get("date"), year, month)
            if not day:
                continue
            raw_time = clean(item.get("gstime") or item.get("gameTime") or item.get("time"))
            gender = clean(item.get("gender") or item.get("genderCode")).lower()
            division = "여자부" if gender in ("f", "2", "female", "women", "여자") else "남자부" if gender in ("m", "1", "male", "men", "남자") else ""
            hs = item.get("hscore", item.get("homeScore", item.get("hpoint", "-")))
            aws = item.get("ascore", item.get("awayScore", item.get("apoint", "-")))
            game_state = item.get("gameStatus") or item.get("status") or item.get("gstatus") or "예정"
            game = make_game(day, raw_time, item.get("hname") or item.get("homeTeamName"), item.get("aname") or item.get("awayTeamName"), hs, aws, f"대한민국 V리그 {division} 프로배구".strip(), "volleyball", "KOVO 공식 API", game_state, item.get("gnum"))
            if game:
                out.append(game)
    return out

def fetch_wkbl(year, month):
    season_year = year - (1 if month < 7 else 0)
    season_code = f"{season_year - 1979:03d}"
    ym = f"{year:04d}{month:02d}"
    base = "https://www.wkbl.or.kr/game/sch/"
    url = f"{base}schedule1.asp?gun=1&season_gu={season_code}&ym={ym}&viewType=1"
    response = SESSION.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    time_map = {}
    list_url = f"{base}inc_list_1_new.asp?season_gu={season_code}&ym={ym}&viewType=2&gun=1"
    try:
        listing = SESSION.get(list_url, timeout=TIMEOUT)
        listing.raise_for_status()
        list_soup = BeautifulSoup(listing.text, "html.parser")
        for tr in list_soup.select("tbody tr"):
            raw_id = clean(tr.get("id", ""))
            if not re.fullmatch(r"\d{8}", raw_id):
                continue
            day = f"{raw_id[:4]}-{raw_id[4:6]}-{raw_id[6:8]}"
            teams = [clean(el.get("data-kr") or el.get_text()) for el in tr.select(".team_name")]
            cells = tr.find_all("td")
            if len(teams) >= 2 and len(cells) >= 4:
                time_map[(day, tuple(sorted(teams[:2])))] = clean(cells[3].get("data-kr") or cells[3].get_text())
    except Exception:
        pass
    out = []
    for td in soup.select("td"):
        day_node = td.select_one(".date_day")
        day_text = clean(day_node.get_text()) if day_node else ""
        if not day_text.isdigit():
            continue
        try:
            day = datetime(year, month, int(day_text)).strftime("%Y-%m-%d")
        except ValueError:
            continue
        for info in td.select(".info_game"):
            teams = [clean(el.get("data-kr") or el.get_text()) for el in info.select("span.language")]
            teams = [x for x in teams if x and x.lower() != "vs" and x != "대"]
            if len(teams) < 2:
                continue
            link = info.select_one("a.txt_info")
            scores = [clean(el.get_text()) for el in link.select("em")] if link else []
            scores = [x for x in scores if x.isdigit()]
            game_state = "취소" if re.search(r"취소|cancel", info.get_text(" ", strip=True), re.I) else ("종료" if len(scores) >= 2 else "예정")
            game_time = time_map.get((day, tuple(sorted(teams[:2]))), "")
            game = make_game(day, game_time, teams[0], teams[1], scores[0] if len(scores) >= 2 else "-", scores[1] if len(scores) >= 2 else "-", "대한민국 WKBL 여자프로농구", "basketball", "WKBL 공식 일정", game_state, link.get("href") if link else "")
            if game:
                out.append(game)
    return out

def fetch_kbo(year, month):
    start, end = month_bounds(year, month)
    out = []
    url = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"
    try:
        SESSION.get("https://www.koreabaseball.com/Schedule/Schedule.aspx", timeout=TIMEOUT)
        response = SESSION.post(url, data={"leId": "1", "srIdList": "0,9,6", "seasonId": str(year), "gameMonth": str(month), "teamId": ""}, headers={"X-Requested-With": "XMLHttpRequest", "Referer": "https://www.koreabaseball.com/Schedule/Schedule.aspx"}, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        current_day = None
        for row in payload.get("rows", []):
            cells = row.get("row", [])
            for cell in cells:
                if clean(cell.get("Class")).lower() == "day":
                    current_day = parse_date(cell.get("Text"), year, month)
            if not current_day:
                continue
            play = next((cell for cell in cells if clean(cell.get("Class")).lower() == "play"), None)
            if not play:
                continue
            fragment = BeautifulSoup(str(play.get("Text") or ""), "html.parser")
            em = fragment.find("em")
            spans = fragment.find_all("span")
            team_spans = [span for span in spans if not em or em not in span.parents]
            names = [clean(span.get_text()) for span in team_spans if clean(span.get_text())]
            score_spans = [clean(span.get_text()) for span in em.find_all("span")] if em else []
            scores = [x for x in score_spans if x.isdigit()]
            if len(names) < 2:
                continue
            time_cell = next((cell for cell in cells if clean(cell.get("Class")).lower() == "time"), None)
            game_time = clean(time_cell.get("Text") if time_cell else "")
            status_text = " ".join(clean(cell.get("Text")) for cell in cells)
            game_state = status(status_text, "종료" if len(scores) >= 2 else "예정")
            game = make_game(current_day, game_time, names[-1], names[0], scores[-1] if len(scores) >= 2 else "-", scores[0] if len(scores) >= 2 else "-", "대한민국 KBO 프로야구", "baseball", "KBO 공식 일정", game_state)
            if game:
                out.append(game)
    except Exception as exc:
        print(f"[WARN] KBO 공식 API 실패: {exc}", file=sys.stderr)
    if not out:
        try:
            fallback = SESSION.get(f"https://raw.githubusercontent.com/dentearl/kbo-data/main/data/kbo/{year}.json", timeout=TIMEOUT)
            fallback.raise_for_status()
            for item in fallback.json():
                day = clean(item.get("officialDate") or item.get("gameDate"))[:10]
                if not day.startswith(f"{year:04d}-{month:02d}"):
                    continue
                home, away = item.get("teams", {}).get("home", {}), item.get("teams", {}).get("away", {})
                game = make_game(day, item.get("gameDate", "")[11:16], home.get("team", {}).get("name"), away.get("team", {}).get("name"), home.get("score", "-"), away.get("score", "-"), "대한민국 KBO 프로야구", "baseball", "KBO 공개 일정 데이터", item.get("status", {}).get("detailedState", "예정"), item.get("gamePk", ""))
                if game:
                    out.append(game)
        except Exception as exc:
            print(f"[WARN] KBO 보조 데이터 실패: {exc}", file=sys.stderr)
    return out

def fetch_espn_korean_football(year, month):
    days = calendar.monthrange(year, month)[1]
    out = []
    leagues = ("kor.1", "kor.2", "kor.k3", "kor.k4", "kor.wk", "kor.national")
    for league in leagues:
        for offset in range(0, days, 7):
            start_dt = datetime(year, month, 1) + timedelta(days=offset)
            end_dt = datetime(year, month, min(days, offset + 7))
            first, last = start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={first}-{last}"
            try:
                response = SESSION.get(url, timeout=TIMEOUT)
                response.raise_for_status()
                payload = response.json()
                for event in payload.get("events", []):
                    comp = (event.get("competitions") or [{}])[0]
                    competitors = comp.get("competitors", [])
                    home = next((x for x in competitors if x.get("homeAway") == "home"), competitors[0] if competitors else {})
                    away = next((x for x in competitors if x.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})
                    day = clean(event.get("date"))[:10]
                    if not day.startswith(f"{year:04d}-{month:02d}"):
                        continue
                    state = (comp.get("status") or {}).get("type", {}).get("shortDetail", "예정")
                    league_name = (event.get("leagues") or [{}])[0].get("name", league)
                    game = make_game(day, clean(event.get("date"))[11:16], (home.get("team") or {}).get("displayName"), (away.get("team") or {}).get("displayName"), home.get("score", "-"), away.get("score", "-"), league_name, "football", "ESPN 국내 축구", state, event.get("id", ""))
                    if game:
                        out.append(game)
            except Exception as exc:
                print(f"[WARN] ESPN {league} {first}-{last} 조회 실패: {exc}", file=sys.stderr)
    return out

def deduplicate(games):
    unique = {}
    for game in games:
        key = (game["date"], game["sport"], game["home"].lower(), game["away"].lower(), game.get("time", ""))
        prior = unique.get(key)
        if prior is None or (prior["homeScore"] == "-" and game["homeScore"] != "-"):
            unique[key] = game
    return sorted(unique.values(), key=lambda g: (g["date"], g.get("time") or "", g["sport"], g["league"], g["home"]))

def main():
    now = datetime.now(KST)
    year, month = now.year, now.month
    providers = {
        "K리그": lambda: fetch_kleague(year, month),
        "KBL": lambda: fetch_kbl(year, month),
        "KOVO": lambda: fetch_kovo(year, month),
        "WKBL": lambda: fetch_wkbl(year, month),
        "KBO": lambda: fetch_kbo(year, month),
        "ESPN 국내 축구": lambda: fetch_espn_korean_football(year, month),
    }
    games, source_status = [], {}
    for name, fn in providers.items():
        try:
            found = fn()
            games.extend(found)
            source_status[name] = {"ok": True, "count": len(found)}
            print(f"[OK] {name}: {len(found)}경기")
        except Exception as exc:
            source_status[name] = {"ok": False, "error": str(exc)[:240]}
            print(f"[WARN] {name}: {exc}", file=sys.stderr)
    games = deduplicate(games)
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            old = {}
    successful = sum(1 for value in source_status.values() if value.get("ok"))
    if successful == 0:
        raise RuntimeError("모든 국내 경기 제공처 조회 실패; 기존 데이터를 보존합니다.")
    if not games and old.get("games") and old.get("month") == f"{year:04d}-{month:02d}":
        raise RuntimeError("새 조회 결과가 비어 있어 기존 국내 경기 데이터를 보존합니다.")
    snapshot = {
        "updatedAt": now.isoformat(timespec="seconds"),
        "month": f"{year:04d}-{month:02d}",
        "timezone": "Asia/Seoul",
        "games": games,
        "sourceStatus": source_status,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUT)
    print(f"[DONE] {len(games)}개 국내 경기 저장: {OUT}")

if __name__ == "__main__":
    main()
