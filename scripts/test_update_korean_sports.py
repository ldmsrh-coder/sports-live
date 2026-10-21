import unittest

from update_korean_sports import deduplicate, make_game, provider_datetime, status


class KoreanSportsCollectorTests(unittest.TestCase):
    def test_utc_start_time_is_converted_to_korean_time(self):
        self.assertEqual(provider_datetime("2026-10-21T10:00:00Z", "2026-10-21"), ("2026-10-21", "19:00"))

    def test_date_only_does_not_invent_midnight(self):
        self.assertEqual(provider_datetime("2026-10-21", "2026-10-21"), ("2026-10-21", ""))

    def test_korean_team_names_are_normalized(self):
        game = make_game("2026-10-21", "19:00", "FC Seoul", "KIA Tigers", "-", "-", "테스트", "soccer", "test")
        self.assertEqual(game["home"], "FC 서울")
        self.assertEqual(game["away"], "KIA 타이거즈")

    def test_status_codes_are_korean(self):
        self.assertEqual(status("FINISHED"), "종료")
        self.assertEqual(status("POSTPONED"), "연기")
        self.assertEqual(status("LIVE"), "진행 중")

    def test_deduplication_keeps_the_version_with_scores(self):
        scheduled = make_game("2026-10-21", "19:00", "FC Seoul", "Gangwon FC", "-", "-", "리그", "soccer", "source-a")
        scored = make_game("2026-10-21", "19:00", "FC Seoul", "Gangwon FC", "2", "1", "리그", "soccer", "source-b")
        result = deduplicate([scheduled, scored])
        self.assertEqual(len(result), 1)
        self.assertEqual((result[0]["homeScore"], result[0]["awayScore"]), ("2", "1"))


if __name__ == "__main__":
    unittest.main()
