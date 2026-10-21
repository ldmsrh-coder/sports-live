import unittest

from update_korean_sports import classify_korean_basketball, deduplicate, make_game, provider_datetime, status


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
