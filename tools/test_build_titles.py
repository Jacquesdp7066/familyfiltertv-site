#!/usr/bin/env python3
"""Checks for the parts of build_titles.py that decide what a parent reads.

Run: python3 tools/test_build_titles.py
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_titles as bt  # noqa: E402

LABELS = {"strong_profanity": "Strong profanity", "mild_profanity": "Mild profanity", "religious": "Religious exclamations"}

TITLE = {
    "videoId": "tt1", "title": "Test Film", "year": 2020, "slug": "test-film-2020",
    "label": "moderate", "labelText": "Moderate", "totalFlagged": 6, "cueCount": 1000,
    "counts": {"strong_profanity": 2, "mild_profanity": 3, "religious": 1},
    "profiles": {"mild": 2, "family": 5, "strict": 5},
    "release": "Test.Film.2020.1080p", "computedAt": "2026-09-25T00:00:00.000Z",
}


def export_record(**overrides):
    record = {
        "videoId": "tt1", "status": "rated", "label": "moderate", "cueCount": 1000,
        "counts": {"strong_profanity": 2, "mild_profanity": 3, "religious": 1},
        "profiles": {"mild": 2, "family": 5, "strict": 5},
        "release": "Test.Film.2020.1080p", "fit": {"ratio": 1.0, "classification": "good"},
        "computedAt": "2026-10-09T00:00:00.000Z",
    }
    record.update(overrides)
    return record


class MaskTerm(unittest.TestCase):
    def test_masks_all_but_the_first_letter(self):
        self.assertEqual(bt.mask_term("fuck", "strong_profanity"), "f***")

    def test_masks_each_word_and_leaves_short_words(self):
        self.assertEqual(bt.mask_term("son of a bitch", "strong_profanity"), "s** of a b****")

    def test_religious_words_stay_readable(self):
        self.assertEqual(bt.mask_term("jesus", "religious"), "jesus")


class AnalysisPanel(unittest.TestCase):
    def test_lists_masked_terms_beside_their_category(self):
        t = dict(TITLE, terms={"strong_profanity": {"shit": 1, "fuck": 1}, "religious": {"god": 1}})
        html = bt.analysis_panel(t, LABELS)
        self.assertIn("<li>Strong profanity: 2 (f*** 1, s*** 1)</li>", html)
        self.assertIn("<li>Religious exclamations: 1 (god 1)</li>", html)
        self.assertIn("<li>Mild profanity: 3</li>", html)
        self.assertNotIn("fuck", html)

    def test_without_terms_shows_totals_only(self):
        self.assertIn("<li>Strong profanity: 2</li>", bt.analysis_panel(TITLE, LABELS))


class Timeline(unittest.TestCase):
    def timeline(self, words, strong):
        return dict(TITLE, timeline={"bucketMs": 600000, "words": words, "strongProfanity": strong})

    def test_absent_data_renders_nothing(self):
        self.assertEqual(bt.timeline_section(TITLE), "")

    def test_names_first_word_first_strong_word_and_heaviest_stretch(self):
        html = bt.timeline_section(self.timeline([1, 0, 4, 1], [0, 0, 2, 0]))
        self.assertIn("comes in the first 10 minutes.", html)
        self.assertIn("The first strong profanity comes between minute 20 and 30.", html)
        self.assertIn("The heaviest stretch is minute 20 to 30, with 4 flagged words.", html)
        self.assertIn("1 of the film's 4 ten-minute stretches have none at all.", html)
        self.assertIn("<tr><td>20 to 30</td><td>4</td><td>2</td></tr>", html)

    def test_says_so_when_there_is_no_strong_profanity(self):
        html = bt.timeline_section(self.timeline([0, 2], [0, 0]))
        self.assertIn("There is no strong profanity anywhere in the film.", html)
        self.assertIn("comes between minute 10 and 20.", html)

    def test_a_tie_for_heaviest_names_the_earlier_stretch(self):
        self.assertIn("minute 0 to 10, with 3", bt.timeline_section(self.timeline([3, 3], [0, 0])))


class Refresh(unittest.TestCase):
    def refresh(self, record, accept=False):
        titles = [copy.deepcopy(TITLE)]
        updated, held = bt.refresh_titles(titles, [record], accept)
        return titles[0], updated, held

    def test_unchanged_analysis_keeps_its_date(self):
        t, updated, held = self.refresh(export_record())
        self.assertEqual((updated, held), ([], []))
        self.assertEqual(t["computedAt"], TITLE["computedAt"])

    def test_new_detail_is_applied_and_dated(self):
        terms = {"strong_profanity": {"fuck": 2}}
        t, updated, held = self.refresh(export_record(terms=terms))
        self.assertEqual(len(updated), 1)
        self.assertEqual(held, [])
        self.assertEqual(t["terms"], terms)
        self.assertEqual(t["computedAt"], "2026-10-09T00:00:00.000Z")

    def test_a_changed_language_level_is_held_back(self):
        record = export_record(label="strong", counts={"strong_profanity": 9}, profiles={"mild": 9, "family": 9, "strict": 9})
        t, updated, held = self.refresh(record)
        self.assertEqual(updated, [])
        self.assertEqual(len(held), 1)
        self.assertEqual(t, TITLE)

    def test_a_large_jump_in_the_count_is_held_back(self):
        record = export_record(counts={"strong_profanity": 2, "mild_profanity": 30, "religious": 1})
        t, updated, held = self.refresh(record)
        self.assertEqual(len(held), 1)
        self.assertEqual(t["totalFlagged"], 6)

    def test_a_small_change_goes_through(self):
        record = export_record(counts={"strong_profanity": 2, "mild_profanity": 4, "religious": 1})
        t, updated, held = self.refresh(record)
        self.assertEqual(held, [])
        self.assertEqual(t["totalFlagged"], 7)

    def test_accept_changes_publishes_a_held_change(self):
        record = export_record(label="strong", counts={"strong_profanity": 9}, profiles={"mild": 9, "family": 9, "strict": 9})
        t, updated, held = self.refresh(record, accept=True)
        self.assertEqual(held, [])
        self.assertEqual((t["label"], t["labelText"], t["totalFlagged"]), ("strong", "Strong", 9))

    def test_an_unusable_export_record_is_ignored(self):
        for bad in (
            export_record(release="Test Film Commentary track", counts={"mild_profanity": 4}),
            export_record(fit={"ratio": 0.8, "classification": "different_cut"}, counts={"mild_profanity": 4}),
            export_record(cueCount=120, counts={"mild_profanity": 4}),
            export_record(status="none", counts={"mild_profanity": 4}),
        ):
            t, updated, held = self.refresh(bad)
            self.assertEqual((t, updated, held), (TITLE, [], []))


if __name__ == "__main__":
    unittest.main()
