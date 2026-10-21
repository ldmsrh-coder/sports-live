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
    "FC Seoul": "FC 서울", "Seoul FC": "FC 서울", "Jeonbuk Hyundai Motors": "전북 현대 모터스",
    "Jeonbuk Hyundai Motors FC": "전북 현대 모터스", "Ulsan HD FC": "울산 HD", "Ulsan Hyundai": "울산 HD",
    "Pohang Steelers": "포항 스틸러스", "Daejeon Hana Citizen": "대전 하나 시티즌",
    "대전": "대전 하나 시티즌", "전북": "전북 현대 모터스", "울산": "울산 HD",
    "포항": "포항 스틸러스", "강원": "강원 FC", "광주": "광주 FC", "제주": "제주 SK FC",
    "Gimcheon Sangmu Football Club": "김천 상무", "Incheon United Club": "인천 유나이티드",
    "Gwangju Football Club": "광주 FC", "Daegu Football Club": "대구 FC",
    "FC Gangneung": "강릉시민축구단", "Seosan FC": "서산 FC",
"Gimhae City": "김해시청 축구단", "Gimhae City FC": "김해시청 축구단",
    "Geoje Citizen": "거제시민축구단", "Jungnang Chorus Mustang FC": "서울중랑축구단",
    "Busan I Park": "부산 아이파크", "Suwon Football Club": "수원 FC",
    "Cheonan City": "천안시티 FC", "Ansan Greeners FC": "안산 그리너스",
    "Paju Frontier FC": "파주 프런티어 FC", "Yongin FC": "용인 FC",
    "Gyeongju Korea Hydro & Nuclear Power WFC": "경주한수원 여자축구단",
    "Seoul Amazones Women": "서울시청 여자축구단",
    "Incheon Hyundai Steel Red Angels Women": "인천 현대제철 레드엔젤스",
    "Gangjin Swans Women": "강진 스완스 여자축구단", "Mungyeong Sangmu WFC": "문경 상무 여자축구단",
    "김천": "김천 상무", "인천": "인천 유나이티드", "서울": "FC 서울", "수원": "수원 삼성 블루윙즈",
    "수원FC": "수원 FC", "부천": "부천 FC 1995", "화성": "화성 FC", "김포": "김포 FC",
    "서울E": "서울 이랜드", "충북청주": "충북청주 FC", "성남": "성남 FC", "천안": "천안시티 FC",
    "안양": "FC 안양", "안산": "안산 그리너스", "아산": "충남 아산", "부산": "부산 아이파크",
    "경남": "경남 FC", "전남": "전남 드래곤즈", "대구": "대구 FC",
    "Daejeon Hana Citizen FC": "대전 하나 시티즌", "Gangwon FC": "강원 FC", "Gwangju FC": "광주 FC",
    "Jeju SK FC": "제주 SK FC", "Jeju United": "제주 유나이티드", "Gimcheon Sangmu": "김천 상무",
    "Gimcheon Sangmu FC": "김천 상무", "FC Anyang": "FC 안양", "Incheon United": "인천 유나이티드",
    "Bucheon FC 1995": "부천 FC 1995", "Suwon FC": "수원 FC", "Suwon Samsung Bluewings": "수원 삼성 블루윙즈",
    "Busan IPark": "부산 아이파크", "Busan I-Park": "부산 아이파크", "Seongnam FC": "성남 FC",
    "Gimpo FC": "김포 FC", "Jeonnam Dragons": "전남 드래곤즈", "Gyeongnam FC": "경남 FC",
    "Chungnam Asan": "충남 아산", "Cheonan City FC": "천안시티 FC", "Ansan Greeners": "안산 그리너스",
    "Seoul E-Land": "서울 이랜드", "Chungbuk Cheongju FC": "충북청주 FC", "Hwaseong FC": "화성 FC",
    "Pyeongtaek Citizen FC": "평택시티즌 FC", "Pyeongchang United FC": "평창유나이티드",
    "Jinju Citizen FC": "진주시민축구단", "Geoje Citizen FC": "거제시민축구단", "Sejong SA FC": "세종SA축구단",
    "Geumsan Ginseng FC": "금산인삼FC", "Jecheon Citizen FC": "제천시민축구단",
    "Namyangju Citizen FC": "남양주시민축구단", "Jincheon HR FC": "진천HRFC", "Yeoju FC": "여주FC",
    "Yangpyeong FC": "양평FC", "Dangjin Citizen FC": "당진시민축구단", "FC Mokpo": "FC목포",
    "Pocheon Citizen FC": "포천시민축구단", "Changwon FC": "창원FC", "Daejeon Korail FC": "대전코레일FC",
    "Gyeongju KHNP FC": "경주한수원FC", "Sihung Citizen FC": "시흥시민축구단",
    "Seoul Jungnang FC": "서울중랑축구단", "Busan Transportation Corporation FC": "부산교통공사 축구단",
    "Suwon FC Women": "수원FC 위민", "Hwacheon KSPO": "화천 KSPO 여자축구단",
    "Incheon Hyundai Steel Red Angels": "인천 현대제철 레드엔젤스", "Seoul City Hall WFC": "서울시청 여자축구단",
    "Boeun Sangmu WFC": "보은 상무 여자축구단", "Sejong Sportstoto WFC": "세종 스포츠토토 여자축구단",
    "Gyeongju KHNP WFC": "경주한수원 여자축구단", "Gumi Sportstoto WFC": "구미 스포츠토토 여자축구단",
    "Changnyeong WFC": "창녕 WFC", "Korea Republic": "대한민국", "Korea Republic U23": "대한민국 U-23 대표팀",
    "Korea Republic U20": "대한민국 U-20 대표팀", "Korea Republic U17": "대한민국 U-17 대표팀",
    "서울 삼성 썬더스": "서울 삼성 썬더스", "서울 SK 나이츠": "서울 SK 나이츠",
    "원주 DB 프로미": "원주 DB 프로미", "고양 소노 스카이거너스": "고양 소노 스카이거너스",
    "수원 KT 소닉붐": "수원 KT 소닉붐", "대구 한국가스공사 페가수스": "대구 한국가스공사 페가수스",
    "창원 LG 세이커스": "창원 LG 세이커스", "부산 KCC 이지스": "부산 KCC 이지스",
    "울산 현대모비스 피버스": "울산 현대모비스 피버스", "안양 정관장 레드부스터스": "안양 정관장 레드부스터스",
    "Seoul SK Knights": "서울 SK 나이츠", "Seoul Samsung Thunders": "서울 삼성 썬더스",
    "Ulsan Mobis Phoebus": "울산 현대모비스 피버스", "Wonju Dongbu Promy": "원주 DB 프로미",
    "Anyang JungKwanJang Red Boosters": "안양 정관장 레드부스터스", "Anyang Jung Kwan Jang Red Boosters": "안양 정관장 레드부스터스",
    "Ulsan Hyundai Mobis Phoebus": "울산 현대모비스 피버스", "Changwon LG Sakers": "창원 LG 세이커스",
    "Busan KCC Egis": "부산 KCC 이지스", "Suwon KT Sonicboom": "수원 KT 소닉붐",
    "Daegu KOGAS Pegasus": "대구 한국가스공사 페가수스", "Wonju DB Promy": "원주 DB 프로미",
    "Anyang Jung Kwan Jang Red Boosters": "안양 정관장 레드부스터스",
    "Dongguk University": "동국대학교", "Chung Ang University": "중앙대학교",
    "Myongji University": "명지대학교", "Konkuk University": "건국대학교",
    "Sungkyunkwan University": "성균관대학교", "Dankook University": "단국대학교",
    "Yonsei University": "연세대학교", "Korea University": "고려대학교",
    "Hanyang University": "한양대학교", "Kyung Hee University": "경희대학교",
    "Sangmyung University": "상명대학교", "Kwangwoon University": "광운대학교",
    "Seoul National University": "서울대학교", "Korea National Sport University": "한국체육대학교",
    "SOOP SOOPers": "SOOP 수퍼스", "SOOPers": "SOOP 수퍼스",
    "Sinhan Bank S-Birds": "신한은행 에스버드", "Shinhan Bank S-Birds": "신한은행 에스버드",
    "Samsunglife Blueminx": "삼성생명 블루밍스", "Samsung Life Blueminx": "삼성생명 블루밍스",
    "Bucheon Keb Hanabank": "부천 하나은행", "Woori Bank Wibee": "우리은행 우리WON",
    "BNK Sum Women": "BNK 썸", "Ulaanbaatar Amazons (W)": "울란바토르 아마존스(여자)",
    "Carleton Ravens (W)": "칼턴 레이븐스(여자)", "Victoria Select Team (W)": "빅토리아 셀렉트팀(여자)",
    "Fujitsu Redwave Women": "후지쯔 레드웨이브(여자)", "South Korea U18 Women": "대한민국 U-18 여자대표팀",
    "New Zealand U18 Women": "뉴질랜드 U-18 여자대표팀", "Philippines U18 Women": "필리핀 U-18 여자대표팀",
    "Australia U18 Women": "호주 U-18 여자대표팀",
    "Goyang Sono Skygunners": "고양 소노 스카이거너스",
    "Woori Bank Woori WON": "우리은행 우리WON", "KB Stars": "KB스타즈",
    "Samsung Life Blueminx": "삼성생명 블루밍스", "Hana Bank": "하나은행",
    "BNK Sum": "BNK 썸", "Shinhan Bank S-Birds": "신한은행 에스버드",
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
    normalized_state = status(state)
    home_score = str(hs) if hs is not None and str(hs) != "" else "-"
    away_score_text = str(away_score) if away_score is not None and str(away_score) != "" else "-"
    if normalized_state in ("예정", "연기", "취소") and home_score in ("0", "0.0", "-") and away_score_text in ("0", "0.0", "-") and ("0" in (home_score, away_score_text) or "0.0" in (home_score, away_score_text)):
        home_score = away_score_text = "-"
    return {
        "id": clean(game_id),
        "date": date,
        "time": time or "시간 미정",
        "home": home,
        "away": away,
        "homeScore": home_score,
        "awayScore": away_score_text,
        "status": normalized_state,
        "league": league,
        "sport": sport,
        "source": source,
        "rawTime": f"{date}T{time}:00+09:00" if time else date,
    }

def provider_datetime(value, default_day):
    raw = clean(value)
    if not raw:
        return default_day, ""
    if len(raw) <= 10:
        return raw[:10].replace("/", "-").replace(".", "-"), ""
    candidate = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=KST)
        parsed = parsed.astimezone(KST)
        return parsed.date().isoformat(), parsed.strftime("%H:%M")
    except (ValueError, TypeError):
        day = raw[:10].replace("/", "-").replace(".", "-")
        clock = raw[11:16] if len(raw) >= 16 and raw[10] == "T" else ""
        return day or default_day, clock

def provider_score(value):
    if isinstance(value, dict):
        for key in ("current", "score", "display", "value", "total"):
            if value.get(key) is not None:
                return str(value[key])
        return "-"
    if isinstance(value, list):
        return str(value[-1]) if value else "-"
    return str(value) if value is not None and str(value) != "" else "-"

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
                item.get("awayGoal", "-"), f"대한민국 K리그 {league_id}부", "soccer",
                "K리그 공식 일정", code, item.get("gameId"),
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

def fetch_kfa_k3_k4(year, month):
    url = f"https://www.kfa.or.kr/live/live.php?act=k3_k4&year={year}&month={month:02d}"
    response = SESSION.get(url, headers={"Referer": "https://www.kfa.or.kr/"}, timeout=TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    aliases = [
        ("FC강릉", "강릉시민축구단"), ("강릉시민축구단", "강릉시민축구단"),
        ("FC목포", "FC목포"), ("경주한수원FC", "경주한수원FC"),
        ("당진시민축구단", "당진시민축구단"), ("대전코레일FC", "대전코레일FC"),
        ("부산교통공사축구단", "부산교통공사 축구단"), ("시흥시민축구단", "시흥시민축구단"),
        ("양평FC", "양평FC"), ("여주FC", "여주FC"), ("울산시민축구단", "울산시민축구단"),
        ("전북현대모터스", "전북 현대 모터스"), ("창원FC", "창원FC"),
        ("춘천시민축구단", "춘천시민축구단"), ("포천시민축구단", "포천시민축구단"),
        ("거제시민축구단", "거제시민축구단"), ("금산인삼FC", "금산인삼FC"),
        ("기장군민축구단", "기장군민축구단"), ("남양주시민축구단", "남양주시민축구단"),
        ("서산에프씨", "서산 FC"), ("서울중랑축구단", "서울중랑축구단"),
        ("세종SA축구단", "세종SA축구단"), ("제천시민축구단", "제천시민축구단"),
        ("진주시민축구단", "진주시민축구단"), ("진천HRFC", "진천HRFC"),
        ("평창유나이티드축구클럽", "평창유나이티드"), ("평택시티즌FC", "평택시티즌 FC"),
        ("함안군민축구단", "함안군민축구단"),
    ]
    candidates = soup.select("li, tr, article, .match-item, .schedule-item, .game-item")
    if not candidates:
        candidates = soup.select("div")
    out, seen = [], set()
    for node in candidates:
        text_value = clean(node.get_text(" ", strip=True))
        if not text_value or len(text_value) > 360 or not re.search(r"K[34]\s*리그|K[34]\s*League", text_value, re.I):
            continue
        date_match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", text_value)
        if date_match:
            day = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
        else:
            short_date = re.search(r"(?<!\d)(\d{1,2})[-./](\d{1,2})(?!\d)", text_value)
            if not short_date:
                continue
            try:
                day = datetime(year, int(short_date.group(1)), int(short_date.group(2))).strftime("%Y-%m-%d")
            except ValueError:
                continue
        if not day.startswith(f"{year:04d}-{month:02d}"):
            continue
        matched = sorted((text_value.find(alias), alias, canonical) for alias, canonical in aliases if text_value.find(alias) >= 0)
        teams, team_ends = [], []
        for pos, alias, canonical in matched:
            if canonical not in teams:
                teams.append(canonical)
                team_ends.append(pos + len(alias))
        if len(teams) < 2:
            continue
        league = "대한민국 K3리그" if re.search(r"K3\s*리그|K3\s*League", text_value, re.I) else "대한민국 K4리그"
        clock_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text_value)
        clock = f"{int(clock_match.group(1)):02d}:{clock_match.group(2)}" if clock_match else ""
        score_nodes = node.select(".score, .home-score, .away-score, .score_home, .score_away")
        scores = [clean(x.get_text(" ", strip=True)) for x in score_nodes if clean(x.get_text(" ", strip=True)).isdigit()]
        if len(scores) < 2 and len(team_ends) >= 2 and day < datetime.now(KST).date().isoformat():
            tail = text_value[max(team_ends[0], team_ends[1]):]
            trailing_numbers = re.findall(r"(?<!\d)\d{1,2}(?!\d)", tail)
            if len(trailing_numbers) >= 2:
                scores = trailing_numbers[:2]
        scored = len(scores) >= 2
        if re.search(r"취소", text_value):
            game_state = "취소"
        elif re.search(r"연기|순연", text_value):
            game_state = "연기"
        elif scored or day < datetime.now(KST).date().isoformat():
            game_state = "종료"
        else:
            game_state = "예정"
        game = make_game(day, clock, teams[0], teams[1], scores[0] if scored else "-", scores[1] if scored else "-",
            league, "soccer", "대한축구협회 K3·K4리그 공식 일정", game_state)
        if game:
            key = (game["date"], game["league"], game["home"], game["away"])
            if key not in seen:
                seen.add(key)
                out.append(game)
    if not out:
        print(f"[WARN] KFA K3·K4 일정에서 {year:04d}-{month:02d} 경기 행을 찾지 못했습니다.", file=sys.stderr)
    return out

def fetch_handball(year, month):
    url = "https://www.koreahandball.com/game/schedule_list.php"
    response = SESSION.get(url, headers={"Referer": "https://www.koreahandball.com/"}, timeout=TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select(".record_table.pc_only table tbody tr")
    if not rows:
        rows = soup.select("table tbody tr")
    if not rows:
        raise RuntimeError("대한핸드볼협회 일정 표를 찾지 못했습니다.")
    current_day = None
    out = []
    for tr in rows:
        cells = tr.find_all(["td", "th"], recursive=False)
        if not cells:
            continue
        first_text = clean(cells[0].get_text(" ", strip=True))
        date_match = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", first_text)
        if date_match:
            current_day = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            time_text = clean(cells[1].get_text(" ", strip=True)) if len(cells) > 1 else ""
            content_cell = cells[3] if len(cells) > 3 else None
            venue = clean(cells[5].get_text(" ", strip=True)) if len(cells) > 5 else ""
        else:
            if not current_day:
                continue
            time_text = first_text
            content_cell = cells[2] if len(cells) > 2 else None
            venue = clean(cells[4].get_text(" ", strip=True)) if len(cells) > 4 else ""
        if not current_day.startswith(f"{year:04d}-{month:02d}") or not content_cell:
            continue
        home_node = content_cell.select_one(".team.home .name")
        away_node = content_cell.select_one(".team.away .name")
        home = clean(home_node.get_text(" ", strip=True)) if home_node else ""
        away = clean(away_node.get_text(" ", strip=True)) if away_node else ""
        if not home or not away:
            continue
        home_score_node = content_cell.select_one(".team.home .score, .score.home, .home .score")
        away_score_node = content_cell.select_one(".team.away .score, .score.away, .away .score")
        hs = clean(home_score_node.get_text(" ", strip=True)) if home_score_node else "-"
        aws = clean(away_score_node.get_text(" ", strip=True)) if away_score_node else "-"
        scored = hs.isdigit() and aws.isdigit()
        game = make_game(current_day, time_text, home, away, hs if scored else "-", aws if scored else "-",
            "대한민국 핸드볼 H리그", "handball", "대한핸드볼협회 공식 일정",
            "종료" if scored else "예정", f"{current_day}-{home}-{away}")
        if game:
            game["venue"] = venue
            out.append(game)
    return out

def fetch_kbo(year, month, league_id='1', league_label='대한민국 KBO 프로야구'):
    start, end = month_bounds(year, month)
    out = []
    url = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"
    try:
        SESSION.get("https://www.koreabaseball.com/Schedule/Schedule.aspx", timeout=TIMEOUT)
        response = SESSION.post(url, data={"leId": league_id, "srIdList": "0,1,2,3,4,5,6,7,8,9", "seasonId": str(year), "gameMonth": str(month), "teamId": ""}, headers={"X-Requested-With": "XMLHttpRequest", "Referer": "https://www.koreabaseball.com/Schedule/Schedule.aspx"}, timeout=TIMEOUT)
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
            time_cell = next((cell for cell in cells if clean(cell.get("Class")).lower() in ("time", "game_time", "gametime")), None)
            game_time = clean(BeautifulSoup(str(time_cell.get("Text") or "") if time_cell else "", "html.parser").get_text(" ", strip=True))
            if not re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", game_time):
                time_match = next((re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", clean(cell.get("Text"))) for cell in cells if re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", clean(cell.get("Text")))), None)
                game_time = time_match.group(0) if time_match else ""
            status_text = " ".join(clean(cell.get("Text")) for cell in cells)
            game_state = status(status_text, "종료" if len(scores) >= 2 else "예정")
            game = make_game(current_day, game_time, names[-1], names[0], scores[-1] if len(scores) >= 2 else "-", scores[0] if len(scores) >= 2 else "-", league_label, "baseball", "KBO 공식 일정", game_state)
            if game:
                out.append(game)
    except Exception as exc:
        print(f"[WARN] KBO 공식 API 실패: {exc}", file=sys.stderr)
    if league_id == '1':
        try:
            fallback_response = SESSION.get(f"https://raw.githubusercontent.com/dentearl/kbo-data/main/data/kbo/{year}.json", timeout=TIMEOUT)
            fallback_response.raise_for_status()
            fallback_games = []
            for item in fallback_response.json():
                official_day = clean(item.get("officialDate") or item.get("gameDate"))[:10]
                raw_game_date = clean(item.get("gameDate") or official_day)
                day, clock = provider_datetime(raw_game_date, official_day)
                if not day.startswith(f"{year:04d}-{month:02d}"):
                    continue
                home, away = item.get("teams", {}).get("home", {}), item.get("teams", {}).get("away", {})
                game = make_game(day, clock, home.get("team", {}).get("name"), away.get("team", {}).get("name"),
                    home.get("score", "-"), away.get("score", "-"), "대한민국 KBO 프로야구", "baseball",
                    "KBO 공개 일정 데이터", item.get("status", {}).get("detailedState", "예정"), item.get("gamePk", ""))
                if game:
                    fallback_games.append(game)
            if not out:
                out = fallback_games
            else:
                for current in out:
                    match = next((g for g in fallback_games if g["date"] == current["date"] and g["home"] == current["home"] and g["away"] == current["away"]), None)
                    if not match:
                        continue
                    if current["time"] == "시간 미정" and match["time"] != "시간 미정":
                        current["time"] = match["time"]
                        current["rawTime"] = match["rawTime"]
                        current["source"] = "KBO 공식 일정 + 공개 데이터"
                    if current["homeScore"] == "-" and match["homeScore"] != "-":
                        current["homeScore"] = match["homeScore"]
                    if current["awayScore"] == "-" and match["awayScore"] != "-":
                        current["awayScore"] = match["awayScore"]
        except Exception as exc:
            print(f"[WARN] KBO 보조 데이터 실패: {exc}", file=sys.stderr)

    return out

def fetch_sportscore_korean_football(year, month):
    today = datetime.now(KST).date()
    month_start = datetime(year, month, 1).date()
    month_end = datetime(year, month, calendar.monthrange(year, month)[1]).date()
    start_day = max(month_start, today)
    end_day = min(month_end, today + timedelta(days=7))
    out = []
    for offset in range((end_day - start_day).days + 1):
        day = (start_day + timedelta(days=offset)).isoformat()
        url = f"https://sportscore.com/api/v1/fixtures/?sport=football&date={day}&limit=200"
        try:
            response = SESSION.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            for item in unpack_array(payload, ("data", "fixtures", "results", "events", "items")):
                competition = item.get("competition") or item.get("league") or item.get("tournament") or {}
                league_name = clean(competition.get("name") if isinstance(competition, dict) else competition)
                country = clean((competition.get("country") or {}).get("name") if isinstance(competition, dict) and isinstance(competition.get("country"), dict) else (competition.get("country") if isinstance(competition, dict) else ""))
                team_home = item.get("home_team") or item.get("homeTeam") or item.get("home") or {}
                team_away = item.get("away_team") or item.get("awayTeam") or item.get("away") or {}
                home_name = team_home.get("name") if isinstance(team_home, dict) else team_home
                away_name = team_away.get("name") if isinstance(team_away, dict) else team_away
                text_to_check = f"{league_name} {country} {home_name} {away_name}".lower()
                if not re.search(r"k league|k[ -]?league|k3 league|k4 league|wk league|korean|korea|대한민국|한국|korea republic", text_to_check):
                    continue
                if re.search(r"k league\s*1|korean k league 1|k리그\s*1", text_to_check):
                    league = "대한민국 K리그 1부"
                elif re.search(r"k league\s*2|korean k league 2|k리그\s*2", text_to_check):
                    league = "대한민국 K리그 2부"
                elif re.search(r"k\s*league\s*3|k3", text_to_check):
                    league = "대한민국 K3리그"
                elif re.search(r"k\s*league\s*4|k4", text_to_check):
                    league = "대한민국 K4리그"
                elif re.search(r"wk league|여자축구", text_to_check):
                    league = "대한민국 WK리그 여자축구"
                elif re.search(r"fa cup|korean cup|코리아컵", text_to_check):
                    league = "대한민국 코리아컵"
                else:
                    league = league_name or "대한민국 국내 축구"
                raw_date = clean(item.get("starting_at") or item.get("start_time") or item.get("date") or item.get("time") or day)
                raw_day, clock = provider_datetime(raw_date, day)
                if raw_day != day:
                    continue
                if not clock:
                    clock = clean(item.get("time"))
                state = item.get("status") or item.get("state") or item.get("status_name") or "예정"
                if isinstance(state, dict):
                    state = state.get("name") or state.get("short_name") or state.get("description") or "예정"
                home_score = provider_score(item.get("home_score", item.get("homeScore", item.get("score_home", "-"))))
                away_score = provider_score(item.get("away_score", item.get("awayScore", item.get("score_away", "-"))))
                game = make_game(day, clock, home_name, away_name, home_score, away_score, league, "soccer", "SportScore 국내 축구", state, item.get("id", ""))
                if game:
                    out.append(game)
        except Exception as exc:
            print(f"[WARN] SportScore {day} 조회 실패: {exc}", file=sys.stderr)
    return out

def classify_korean_basketball(league_name, country_name):
    competition = clean(league_name).lower()
    country = clean(country_name).lower()
    if re.search(r"\bwkbl\b", competition):
        return "대한민국 WKBL 여자프로농구"
    if re.search(r"\bkbl\b.*d.?league|d.?league.*\bkbl\b", competition):
        return "대한민국 KBL D리그"
    if re.search(r"\bkbl\b|korean professional basketball|korean basketball league", competition):
        return "대한민국 KBL 프로농구"
    if re.search(r"university|college|u-league|대학", competition) and re.search(r"korea|대한민국|한국", country + " " + competition):
        return "대한민국 대학농구 U리그"
    return ""

def fetch_sportscore_korean_basketball(year, month):
    today = datetime.now(KST).date()
    month_start = datetime(year, month, 1).date()
    month_end = datetime(year, month, calendar.monthrange(year, month)[1]).date()
    start_day = month_start
    end_day = month_end
    out = []
    for offset in range((end_day - start_day).days + 1):
        day = (start_day + timedelta(days=offset)).isoformat()
        url = f"https://sportscore.com/api/v1/fixtures/?sport=basketball&date={day}&limit=200"
        try:
            response = SESSION.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            for item in unpack_array(payload, ("data", "fixtures", "results", "events", "items")):
                competition = item.get("competition") or item.get("league") or item.get("tournament") or {}
                league_name = clean(competition.get("name") if isinstance(competition, dict) else competition)
                country_value = competition.get("country") if isinstance(competition, dict) else ""
                country_name = clean(country_value.get("name") if isinstance(country_value, dict) else country_value)
                home_obj = item.get("home_team") or item.get("homeTeam") or item.get("home") or {}
                away_obj = item.get("away_team") or item.get("awayTeam") or item.get("away") or {}
                home_name = home_obj.get("name") if isinstance(home_obj, dict) else home_obj
                away_name = away_obj.get("name") if isinstance(away_obj, dict) else away_obj
                league = classify_korean_basketball(league_name, country_name)
                if not league:
                    continue
                raw_date = clean(item.get("starting_at") or item.get("start_time") or item.get("date") or item.get("time") or day)
                raw_day, clock = provider_datetime(raw_date, day)
                if raw_day != day:
                    continue
                if not clock:
                    clock = clean(item.get("time"))
                game_state = item.get("status") or item.get("state") or "예정"
                if isinstance(game_state, dict):
                    game_state = game_state.get("name") or game_state.get("short_name") or game_state.get("description") or "예정"
                game = make_game(day, clock, home_name, away_name,
                    provider_score(item.get("home_score", item.get("homeScore", "-"))),
                    provider_score(item.get("away_score", item.get("awayScore", "-"))),
                    league, "basketball", "SportScore 국내 농구",
                    game_state, item.get("id", ""))
                if game:
                    out.append(game)
        except Exception as exc:
            print(f"[WARN] SportScore 농구 {day} 조회 실패: {exc}", file=sys.stderr)
    return out

def deduplicate(games):
    unique = {}
    for game in games:
        league_key = game["league"] if game["sport"] == "baseball" else ""
        time_key = game.get("time", "") if game["sport"] == "baseball" else ""
        key = (game["date"], game["sport"], game["home"].lower(), game["away"].lower(), league_key, time_key)
        prior = unique.get(key)
        if prior is None:
            unique[key] = game
            continue
        improved = False
        if prior["time"] == "시간 미정" and game["time"] != "시간 미정":
            prior["time"], prior["rawTime"] = game["time"], game["rawTime"]
            improved = True
        for field in ("homeScore", "awayScore"):
            if prior[field] == "-" and game[field] != "-":
                prior[field] = game[field]
                improved = True
        if prior["status"] == "예정" and game["status"] not in ("예정", "시간 미정"):
            prior["status"] = game["status"]
            improved = True
        if improved:
            sources = []
            for source_name in (prior.get("source", ""), game.get("source", "")):
                for item in source_name.split(" + "):
                    if item and item not in sources:
                        sources.append(item)
            prior["source"] = " + ".join(sources)
    return sorted(unique.values(), key=lambda g: (g["date"], g.get("time") or "", g["sport"], g["league"], g["home"]))

def main():
    now = datetime.now(KST)
    year, month = now.year, now.month
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    months = [(year, month), (next_year, next_month)]
    current_month = f"{year:04d}-{month:02d}"
    month_labels = [f"{y:04d}-{m:02d}" for y, m in months]
    providers = {
        "K리그": fetch_kleague,
        "KFA K3·K4": fetch_kfa_k3_k4,
        "KOVO": fetch_kovo,
        "핸드볼": fetch_handball,
        "WKBL": fetch_wkbl,
        "KBO": lambda y, m: fetch_kbo(y, m),
        "KBO 퓨처스리그": lambda y, m: fetch_kbo(y, m, "2", "대한민국 KBO 퓨처스리그"),
        "SportScore 국내 축구": fetch_sportscore_korean_football,
        "SportScore 국내 농구": fetch_sportscore_korean_basketball,
    }
    games, source_status = [], {}
    for name, fn in providers.items():
        periods = [months[0]] if name.startswith("SportScore") else months
        found_all, outcomes, failures = [], [], []
        for y, m in periods:
            try:
                found = fn(y, m)
                found_all.extend(found)
                outcomes.append(True)
                print(f"[OK] {name} {y:04d}-{m:02d}: {len(found)}경기")
            except Exception as exc:
                outcomes.append(False)
                failures.append(f"{y:04d}-{m:02d}: {str(exc)[:180]}")
                print(f"[WARN] {name} {y:04d}-{m:02d}: {exc}", file=sys.stderr)
        games.extend(found_all)
        source_status[name] = {
            "ok": bool(outcomes) and all(outcomes),
            "count": len(found_all),
            "months": [f"{y:04d}-{m:02d}" for y, m in periods],
            "errors": failures,
        }
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
    old_months = old.get("months") or ([old.get("month")] if old.get("month") else [])
    if not games and old.get("games") and current_month in old_months:
        raise RuntimeError("새 조회 결과가 비어 있어 기존 국내 경기 데이터를 보존합니다.")
    snapshot = {
        "updatedAt": now.isoformat(timespec="seconds"),
        "month": current_month,
        "months": month_labels,
        "timezone": "Asia/Seoul",
        "games": games,
        "sourceStatus": source_status,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUT)
    print(f"[DONE] {len(games)}개 국내 경기 저장 ({', '.join(month_labels)}): {OUT}")

if __name__ == "__main__":
    main()
