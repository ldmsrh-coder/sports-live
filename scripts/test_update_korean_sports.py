import unittest
from unittest.mock import patch

from update_korean_sports import classify_korean_basketball, deduplicate, fetch_kfa_k3_k4, make_game, provider_datetime, status


class KoreanSportsCollectorTests(unittest.TestCase):
    def test_utc_start_time_is_converted_to_korean_time(self):
        self.assertEqual(provider_datetime("2026-10-21T10:00:00Z", "2026-10-21"), ("2026-10-21", "19:00"))

    def test_date_only_does_not_invent_midnight(self):
        self.assertEqual(provider_datetime("2026-10-21", "2026-10-21"), ("2026-10-21", ""))

    def test_korean_team_names_are_normalized(self):
        game = make_game("2026-10-21", "19:00", "FC Seoul", "KIA Tigers", "-", "-", "테스트", "soccer", "test")
        self.assertEqual(game["home"], "FC 서울")
        self.assertEqual(game["away"], "KIA 타이거즈")

    def test_domestic_and_tournament_team_aliases_are_korean(self):
        game = make_game("2026-10-21", "19:00", "Sinhan Bank S-Birds", "Ulaanbaatar Amazons (W)", "-", "-", "WKBL", "basketball", "test")
        self.assertEqual(game["home"], "신한은행 에스버드")
        self.assertEqual(game["away"], "울란바토르 아마존스(여자)")

    def test_official_k3_k4_schedule_parser(self):
        class FakeResponse:
            ok = True
            text = "<ul><li>2026 K3리그 25라운드 토요일 10-31 14:00 시흥시민축구단 포천시민축구단</li></ul>"
            def raise_for_status(self):
                return None
        with patch("update_korean_sports.SESSION.get", return_value=FakeResponse()):
            games = fetch_kfa_k3_k4(2026, 10)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["league"], "대한민국 K3리그")
        self.assertEqual(games[0]["date"], "2026-10-31")
        self.assertEqual(games[0]["time"], "14:00")

    def test_schedule_and_live_result_records_merge(self):
        scheduled = make_game("2026-10-21", "", "시흥시민축구단", "포천시민축구단", "-", "-", "대한민국 K3리그", "soccer", "KFA")
        result = make_game("2026-10-21", "14:00", "시흥시민축구단", "포천시민축구단", "2", "1", "대한민국 K3리그", "soccer", "SportScore", "종료")
        merged = deduplicate([scheduled, result])
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0]["time"], merged[0]["homeScore"], merged[0]["awayScore"]), ("14:00", "2", "1"))
        self.assertIn("KFA", merged[0]["source"])
        self.assertIn("SportScore", merged[0]["source"])

    def test_official_k3_k4_result_scores_are_parsed(self):
        class FakeResponse:
            ok = True
            text = "<ul><li>2026 K3리그 24라운드 토요일 10-10 시흥시민축구단 포천시민축구단 2 1</li></ul>"
            def raise_for_status(self):
                return None
        with patch("update_korean_sports.SESSION.get", return_value=FakeResponse()):
            games = fetch_kfa_k3_k4(2026, 10)
        match = next(g for g in games if g["date"] == "2026-10-10")
        self.assertEqual((match["homeScore"], match["awayScore"]), ("2", "1"))
        self.assertEqual(match["status"], "종료")

    def test_status_codes_are_korean(self):
        self.assertEqual(status("FINISHED"), "종료")
        self.assertEqual(status("POSTPONED"), "연기")
        self.assertEqual(status("LIVE"), "진행 중")

    def test_basketball_competitions_are_classified_by_league_not_team_gender(self):
        self.assertEqual(classify_korean_basketball("KBL", "South Korea"), "대한민국 KBL 프로농구")
        self.assertEqual(classify_korean_basketball("WKBL", "South Korea"), "대한민국 WKBL 여자프로농구")
        self.assertEqual(classify_korean_basketball("Korea University League", "South Korea"), "대한민국 대학농구 U리그")
        self.assertEqual(classify_korean_basketball("Women's International Friendly", "South Korea"), "")

    def test_deduplication_keeps_the_version_with_scores(self):
        scheduled = make_game("2026-10-21", "19:00", "FC Seoul", "Gangwon FC", "-", "-", "리그", "soccer", "source-a")
        scored = make_game("2026-10-21", "19:00", "FC Seoul", "Gangwon FC", "2", "1", "리그", "soccer", "source-b")
        result = deduplicate([scheduled, scored])
        self.assertEqual(len(result), 1)
        self.assertEqual((result[0]["homeScore"], result[0]["awayScore"]), ("2", "1"))


if __name__ == "__main__":
    unittest.main()
