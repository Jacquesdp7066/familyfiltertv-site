#!/usr/bin/env python3
"""Checks for the parts of build_titles.py that decide what a parent reads.

Run: python3 tools/test_build_titles.py
"""
import copy
import html.parser
import json
import os
import re
import sys
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_titles as bt  # noqa: E402
import weekly_refresh as wr  # noqa: E402

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


class UntrustedExport(unittest.TestCase):
    """The export comes from the database, so nothing in it reaches a page unchecked."""

    HOSTILE = "<script>alert(1)</script>"

    def assert_rejected(self, record):
        titles = [copy.deepcopy(TITLE)]
        updated, held = bt.refresh_titles(titles, [record], accept_changes=True)
        self.assertEqual(updated, [])
        self.assertEqual(len(held), 1)
        self.assertIn("REJECTED", held[0])
        self.assertEqual(titles[0], TITLE)

    def test_a_well_formed_record_has_no_problems(self):
        record = export_record(
            terms={"strong_profanity": {"fuck": 2}},
            timeline={"bucketMs": 600000, "words": [2, 4], "strongProfanity": [2, 0]},
        )
        self.assertEqual(bt.analysis_problems(record), [])

    def test_markup_in_a_count_is_rejected(self):
        self.assert_rejected(export_record(counts={"mild_profanity": self.HOSTILE}))

    def test_an_unknown_category_is_rejected(self):
        self.assert_rejected(export_record(counts={self.HOSTILE: 4}))

    def test_markup_in_a_profile_name_is_rejected(self):
        self.assert_rejected(export_record(profiles={self.HOSTILE: 1, "family": 5, "strict": 5}))

    def test_markup_in_a_profile_count_is_rejected(self):
        self.assert_rejected(export_record(profiles={"mild": self.HOSTILE, "family": 5, "strict": 5}))

    def test_markup_in_the_line_count_is_rejected(self):
        self.assert_rejected(export_record(cueCount=self.HOSTILE))

    def test_an_unknown_language_level_is_rejected(self):
        self.assert_rejected(export_record(label=self.HOSTILE))

    def test_markup_in_a_term_count_is_rejected(self):
        self.assert_rejected(export_record(terms={"strong_profanity": {"fuck": self.HOSTILE}}))

    def test_markup_in_the_timeline_is_rejected(self):
        self.assert_rejected(export_record(timeline={"bucketMs": 600000, "words": [self.HOSTILE], "strongProfanity": [0]}))
        self.assert_rejected(export_record(timeline={"bucketMs": self.HOSTILE, "words": [1], "strongProfanity": [0]}))

    def test_markup_in_the_date_is_rejected(self):
        self.assert_rejected(export_record(computedAt=self.HOSTILE, counts={"mild_profanity": 4}))

    def test_a_true_false_value_is_not_a_count(self):
        self.assert_rejected(export_record(counts={"mild_profanity": True}))

    def test_series_episodes_are_left_out_of_the_film_comparison(self):
        film = export_record(type="movie")
        episode = export_record(videoId="tt9:1:1", type="series")
        self.assertEqual(bt.build_benchmark([film, episode]), {"filmCount": 1, "totals": [6]})

    def test_a_malformed_record_is_left_out_of_the_comparison_data(self):
        good = export_record()
        bad = export_record(videoId="tt2", counts={"mild_profanity": self.HOSTILE})
        self.assertEqual(bt.build_benchmark([good, bad]), {"filmCount": 1, "totals": [6]})

    def test_a_term_name_with_markup_is_escaped_on_the_page(self):
        t = dict(TITLE, terms={"religious": {self.HOSTILE: 1}})
        html = bt.analysis_panel(t, LABELS)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_a_title_file_with_a_malformed_analysis_stops_the_build(self):
        with self.assertRaises(SystemExit):
            bt.check_titles([dict(TITLE, counts={"mild_profanity": self.HOSTILE})])
        bt.check_titles([TITLE])


class ExportValues(unittest.TestCase):
    def test_turns_a_database_query_result_into_plain_rows(self):
        results = [
            {"readTime": "2026-10-09T00:00:00Z"},
            {"document": {
                "name": "projects/p/databases/(default)/documents/ratings/tt1",
                "fields": {
                    "status": {"stringValue": "rated"},
                    "cueCount": {"integerValue": "1000"},
                    "counts": {"mapValue": {"fields": {"mild_profanity": {"integerValue": "3"}}}},
                    "computedAt": {"timestampValue": "2026-10-09T00:00:00.000Z"},
                    "fit": {"mapValue": {"fields": {"ratio": {"doubleValue": 1.0}, "classification": {"stringValue": "good"}}}},
                    "timeline": {"mapValue": {"fields": {
                        "bucketMs": {"integerValue": "600000"},
                        "words": {"arrayValue": {"values": [{"integerValue": "3"}, {"integerValue": "0"}]}},
                        "strongProfanity": {"arrayValue": {"values": [{"integerValue": "0"}, {"integerValue": "0"}]}},
                    }}},
                    "terms": {"mapValue": {}},
                },
            }},
        ]
        self.assertEqual(wr.rows_from_query(results), [{
            "videoId": "tt1", "status": "rated", "cueCount": 1000, "counts": {"mild_profanity": 3},
            "computedAt": "2026-10-09T00:00:00.000Z", "fit": {"ratio": 1.0, "classification": "good"},
            "timeline": {"bucketMs": 600000, "words": [3, 0], "strongProfanity": [0, 0]}, "terms": {},
        }])

    def test_the_report_lists_held_and_rejected_lines_and_never_accepts_them(self):
        log = "updated  A: mild 3 -> mild 4\nHELD     B: mild 3 -> strong 40  (check)\nREJECTED C: counts\ngenerated 20"
        body = wr.report_body(log, 3)
        self.assertIn("Files changed: 3", body)
        for line in ("updated  A", "HELD     B", "REJECTED C"):
            self.assertIn(line, body)
        self.assertNotIn("generated 20", body)


FULL = dict(
    TITLE,
    genres=["Comedy"], runtime="100 min", imdbUrl="https://www.imdb.com/title/tt1/", labelText="Moderate",
    intro="A test film.", related=[], terms={"strong_profanity": {"fuck": 1, "fucking": 1}},
    timeline={"bucketMs": 600000, "words": [1, 0, 4, 1], "strongProfanity": [0, 0, 2, 0]},
)
BENCHMARK = {"filmCount": 5, "totals": [0, 2, 6, 40, 100]}
CLEAN = dict(FULL, title="Clean Film", slug="clean-film-2020", totalFlagged=0, counts={}, terms={},
             profiles={"mild": 0, "family": 0, "strict": 0}, label="clean", labelText="Clean",
             timeline={"bucketMs": 600000, "words": [0, 0], "strongProfanity": [0, 0]})


class Visible(html.parser.HTMLParser):
    """Collects the text of the <h3> questions and the <p> answers inside the .faq block."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.tag = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == "div" and ("class", "faq") in attrs:
            self.depth = 1
        elif self.depth and tag == "div":
            self.depth += 1
        elif self.depth and tag in ("h3", "p"):
            self.tag = tag

    def handle_endtag(self, tag):
        if self.depth and tag == "div":
            self.depth -= 1
        self.tag = None

    def handle_data(self, data):
        if self.tag:
            self.items.append(data)


def jsonld_blocks(page):
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', page, re.S)]


class SearchTitle(unittest.TestCase):
    def test_a_title_with_words_asks_how_many_and_keeps_the_brand_when_it_fits(self):
        t = dict(FULL, title="Up", year=2009)
        with unittest.mock.patch.object(bt, "TITLE_LIMIT", 70):
            self.assertEqual(bt.seo_title(t), "How Many Swear Words in Up (2009)? Parents Guide | Family Filter TV")
        self.assertEqual(bt.seo_title(t), "How Many Swear Words in Up (2009)? Parents Guide")  # 67 > 65
        self.assertEqual(bt.seo_h1(t), "How many swear words are in Up (2009)?")

    def test_a_long_title_drops_the_brand_suffix(self):
        self.assertEqual(bt.seo_title(FULL), "How Many Swear Words in Test Film (2020)? Parents Guide")

    def test_a_film_with_no_flagged_words_asks_whether_it_has_any_swearing(self):
        t = dict(CLEAN, title="Up", year=2009)
        with unittest.mock.patch.object(bt, "TITLE_LIMIT", 70):
            self.assertEqual(bt.seo_title(t), "Does Up (2009) Have Any Swearing? Parents Guide | Family Filter TV")
        self.assertEqual(bt.seo_title(CLEAN), "Does Clean Film (2020) Have Any Swearing? Parents Guide")
        self.assertEqual(bt.seo_h1(CLEAN), "Does Clean Film (2020) have any swearing?")

    def test_a_very_long_title_keeps_only_the_question(self):
        t = dict(FULL, title="Ant-Man and the Wasp: Quantumania", year=2023)
        self.assertEqual(
            bt.seo_title(t), "How Many Swear Words in Ant-Man and the Wasp: Quantumania (2023)?")

    def test_the_page_carries_the_title_h1_and_a_parents_guide_description(self):
        page = bt.title_page_html(FULL, {FULL["videoId"]: FULL}, LABELS, BENCHMARK)
        self.assertIn(f"<title>{bt.seo_title(FULL)}</title>", page)
        self.assertIn(f"<h1 class=\"page-title\">{bt.seo_h1(FULL)}</h1>", page)
        self.assertIn(f'<meta property="og:title" content="{bt.seo_title(FULL)}">', page)
        self.assertIn("arents guide", re.search(r'name="description" content="([^"]*)"', page).group(1))
        self.assertIn("Parents guide: swearing and language", page)


class AnswerFirst(unittest.TestCase):
    def test_the_lead_gives_the_total_the_strong_count_and_the_f_word_count(self):
        sentence, detail = bt.answer_lead(FULL)
        self.assertIn("has 6 flagged words", sentence)
        self.assertEqual(detail, "Strong profanity: 2. F-word: 2.")

    def test_the_f_word_counts_every_flagged_form_of_it(self):
        t = dict(FULL, terms={"strong_profanity": {"fuck": 3, "motherfucker": 2, "shit": 9}})
        self.assertEqual(bt.fword_count(t), 5)

    def test_the_f_word_line_is_left_out_when_the_record_has_no_per_word_detail(self):
        t = {k: v for k, v in FULL.items() if k != "terms"}
        self.assertEqual(bt.answer_lead(t)[1], "Strong profanity: 2.")

    def test_a_film_with_none_says_so_in_the_first_sentence(self):
        sentence, detail = bt.answer_lead(CLEAN)
        self.assertIn("no flagged swearing", sentence)
        self.assertEqual(detail, "Strong profanity: 0. F-word: 0.")


class Faq(unittest.TestCase):
    def test_the_json_ld_matches_the_visible_questions_and_answers(self):
        page = bt.title_page_html(FULL, {FULL["videoId"]: FULL}, LABELS, BENCHMARK)
        parser = Visible()
        parser.feed(page)
        faq = next(b for b in jsonld_blocks(page) if b["@type"] == "FAQPage")
        expected = [x for q in faq["mainEntity"] for x in (q["name"], q["acceptedAnswer"]["text"])]
        self.assertEqual(parser.items, expected)
        self.assertTrue(4 <= len(faq["mainEntity"]) <= 6)

    def test_a_clean_film_gets_a_faq_too(self):
        items = bt.faq_items(CLEAN, LABELS, BENCHMARK)
        self.assertTrue(4 <= len(items) <= 6)
        self.assertIn("No.", dict(items)["Does Clean Film use the F-word?"])

    def test_the_timeline_answer_names_a_ten_minute_stretch_and_no_exact_time(self):
        answer = dict(bt.faq_items(FULL, LABELS, BENCHMARK))["Where in Test Film is the swearing heaviest?"]
        self.assertIn("between minute 20 and 30", answer)
        self.assertIsNone(re.search(r"\d+:\d\d", answer))

    def test_the_comparison_answer_uses_the_benchmark(self):
        answer = dict(bt.faq_items(FULL, LABELS, BENCHMARK))["How does Test Film compare with the average film?"]
        self.assertIn("more flagged language than 40% of the 5 films", answer)

    def test_the_f_word_answer_masks_the_words(self):
        answer = dict(bt.faq_items(FULL, LABELS, BENCHMARK))["Does Test Film use the F-word?"]
        self.assertIn("f*** 1", answer)
        self.assertNotIn("fuck", answer)


class StructuredData(unittest.TestCase):
    def test_every_block_parses_and_the_page_node_has_a_modified_date_and_publisher(self):
        page = bt.title_page_html(FULL, {FULL["videoId"]: FULL}, LABELS, BENCHMARK)
        blocks = {b["@type"]: b for b in jsonld_blocks(page)}
        self.assertEqual(set(blocks), {"Movie", "WebPage", "BreadcrumbList", "FAQPage"})
        self.assertEqual(blocks["WebPage"]["dateModified"], "2026-09-25T00:00:00.000Z")
        self.assertEqual(blocks["WebPage"]["publisher"]["@type"], "Organization")
        self.assertEqual(blocks["WebPage"]["about"]["@id"], blocks["Movie"]["@id"])


class Methodology(unittest.TestCase):
    def test_a_film_page_links_to_the_methodology_page(self):
        page = bt.title_page_html(FULL, {FULL["videoId"]: FULL}, LABELS, BENCHMARK)
        self.assertIn('<a href="../methodology/">How we count swear words</a>', page)

    def test_the_methodology_page_lists_the_categories_and_parses(self):
        all_labels = dict(LABELS, crude="Crude language")
        page = bt.methodology_page_html([FULL], all_labels)
        self.assertIn("<td>Strong profanity</td><td>Yes</td><td>Yes</td><td>Yes</td>", page)
        self.assertIn("<td>Crude language</td><td>No</td><td>No</td><td>Yes</td>", page)
        self.assertEqual({b["@type"] for b in jsonld_blocks(page)}, {"WebPage", "BreadcrumbList"})

    def test_a_film_cannot_take_the_methodology_slug(self):
        with self.assertRaises(SystemExit):
            bt.check_titles([dict(FULL, slug="methodology")])


class LowCount(unittest.TestCase):
    def test_a_clean_film_explains_what_was_checked_and_links_other_low_films(self):
        other = dict(CLEAN, videoId="tt2", title="Other Clean", slug="other-clean-2020")
        html_ = bt.low_count_section(CLEAN, {"tt1": CLEAN, "tt2": other}, LABELS)
        self.assertIn("all 2 ten-minute stretches", html_)
        self.assertIn('<a href="../other-clean-2020/">Other Clean (2020)</a>', html_)
        self.assertIn("Strict filter</strong> mutes every category. In Clean Film: 0 of 1,000 lines muted", html_)

    def test_a_busier_film_gets_no_such_section(self):
        self.assertEqual(bt.low_count_section(FULL, {"tt1": FULL}, LABELS), "")



class ResultBlock(unittest.TestCase):
    def test_total_label_and_one_bar_per_category(self):
        html = bt.result_block(FULL, LABELS)
        self.assertIn('<span class="result-figure">6</span>', html)
        self.assertIn("pill pill-moderate", html)
        nums = [int(n) for n in re.findall(r'<span class="bar-num">(\d+)</span>', html)]
        self.assertEqual(nums, [2, 3, 1])
        self.assertEqual(sum(nums), FULL["totalFlagged"])

    def test_bars_are_relative_to_the_largest_category(self):
        widths = [float(w) for w in re.findall(r"width:([\d.]+)%", bt.result_block(FULL, LABELS))]
        self.assertEqual(widths, [66.7, 100.0, 33.3])

    def test_a_clean_film_gets_a_calm_state_and_no_bars(self):
        html = bt.result_block(CLEAN, LABELS)
        self.assertIn("No flagged words", html)
        self.assertIn("pill-clean", html)
        self.assertNotIn("bar-row", html)
        self.assertNotIn("result-figure", html)

    def test_real_data_bars_sum_to_the_total(self):
        with open(bt.DATA_PATH) as f:
            data = json.load(f)
        for t in data["titles"]:
            html = bt.result_block(t, data["categoryLabels"])
            if t["totalFlagged"]:
                nums = [int(n) for n in re.findall(r'<span class="bar-num">(\d+)</span>', html)]
                self.assertEqual(sum(nums), t["totalFlagged"], t["slug"])


class Chart(unittest.TestCase):
    WORDS, STRONG = [1, 0, 4, 1], [0, 0, 2, 0]

    def chart(self, words=None, strong=None):
        t = dict(FULL, timeline={"bucketMs": 600000, "words": words or self.WORDS, "strongProfanity": strong or self.STRONG})
        return bt.timeline_chart(t)

    def test_one_bar_group_per_bucket(self):
        self.assertEqual(self.chart().count("<g><title>"), 4)
        self.assertEqual(self.chart([1] * 13, [0] * 13).count("<g><title>"), 13)

    def test_strong_buckets_are_hushed_and_marked(self):
        html = self.chart()
        self.assertEqual(html.count('class="mark"'), 1)
        self.assertIn('class="hush"', html)
        self.assertEqual(html.count('class="bar"'), 2)

    def test_tallest_bar_fills_the_plot_and_others_scale_to_it(self):
        heights = [float(h) for h in re.findall(r'class="bar" [^>]*height="([\d.]+)"', self.chart([4, 2, 0, 1], [0] * 4))]
        self.assertEqual(heights[0], bt.CHART_H - bt.CHART_TOP - bt.CHART_BOTTOM)
        self.assertAlmostEqual(heights[1] * 2, heights[0], places=0)

    def test_aria_label_and_desc_come_from_the_data(self):
        html = self.chart()
        self.assertIn('role="img"', html)
        label = re.search(r'aria-label="([^"]+)"', html).group(1)
        self.assertIn("4 stretches, from 0 to 4 flagged words, busiest at minute 20 to 30", label)
        self.assertIn("Strong profanity appears in 1 stretch, first between minute 20 and 30.", label)
        self.assertIn(f"<desc>{label}</desc>", html)
        self.assertIn("<title>Flagged words per ten-minute stretch of Test Film</title>", html)
        self.assertIn("No stretch has strong profanity.", self.chart([2, 1], [0, 0]))

    def test_axis_labels_are_whole_minutes_and_few(self):
        html = self.chart([1] * 25, [0] * 25)
        ticks = re.findall(r'class="axis" x="[\d.]+" y="[\d.]+" text-anchor="middle">(\d+)</text>', html)
        self.assertEqual(ticks[:3], ["0", "40", "80"])
        self.assertLessEqual(len(ticks), 8)

    def test_table_stays_in_the_page_inside_a_disclosure(self):
        html = bt.timeline_section(dict(FULL, timeline={"bucketMs": 600000, "words": self.WORDS, "strongProfanity": self.STRONG}))
        self.assertIn("<summary>See the numbers</summary>", html)
        self.assertIn("<tr><td>20 to 30</td><td>4</td><td>2</td></tr>", html)
        self.assertLess(html.index("<svg"), html.index("<table>"))

    def test_clean_film_has_no_chart(self):
        self.assertEqual(bt.timeline_section(CLEAN), "")


class ProfileTiles(unittest.TestCase):
    def test_three_tiles_keep_the_same_words(self):
        html = bt.analysis_panel(TITLE, LABELS)
        self.assertEqual(html.count('class="tile"'), 3)
        text = re.sub(r"<[^>]+>", "", html)
        for line in ("Mild filter: 2 of 1000 subtitle lines muted", "Strict filter: 5 of 1000 subtitle lines muted"):
            self.assertIn(line, re.sub(r"\s+", " ", text))


class FilmCss(unittest.TestCase):
    def test_film_pages_link_film_css_one_level_up(self):
        page = bt.title_page_html(FULL, {FULL["videoId"]: FULL}, LABELS, BENCHMARK)
        self.assertIn('<link rel="stylesheet" href="../film.css">', page)
        self.assertIn('href="../../style.css"', page)
        self.assertLess(page.index("<svg"), page.index("<table>"))

    def test_result_block_sits_under_the_lead(self):
        page = bt.title_page_html(FULL, {FULL["videoId"]: FULL}, LABELS, BENCHMARK)
        self.assertLess(page.index('class="lead"'), page.index('class="result"'))
        self.assertLess(page.index('class="result"'), page.index('<section class="panel"'))

    def test_film_css_exists(self):
        self.assertTrue(os.path.exists(os.path.join(bt.ROOT, "titles", "film.css")))

    def test_index_links_film_css_and_keeps_search_rows(self):
        titles = [dict(FULL), dict(CLEAN)]
        page = bt.index_page_html(titles, LABELS)
        self.assertIn('<link rel="stylesheet" href="film.css">', page)
        self.assertEqual(page.count('class="title-row" data-search="'), 2)
        self.assertIn('data-search="test film"', page)
        self.assertIn("6 flagged words", page)
        self.assertIn("0 flagged words", page)
        self.assertIn("document.querySelectorAll('.title-row')", page)


class SitemapAndLlms(unittest.TestCase):
    def run_in_tmp(self, name, content, update):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, name)
            with open(path, "w") as f:
                f.write(content)
            attr = "SITEMAP_PATH" if name.endswith(".xml") else "LLMS_PATH"
            with unittest.mock.patch.object(bt, attr, path):
                changed = update([FULL])
                again = update([FULL])
            with open(path) as f:
                return f.read(), changed, again

    def test_the_sitemap_lists_the_methodology_page_and_a_rerun_changes_nothing(self):
        stub = "<urlset>\n  <url><loc>https://familyfiltertv.com/</loc></url>\n  <url><loc>https://familyfiltertv.com/install.html</loc></url>\n</urlset>\n"
        out, changed, again = self.run_in_tmp("sitemap.xml", stub, bt.update_sitemap)
        self.assertIn("/titles/methodology/</loc>", out)
        self.assertTrue(changed)
        self.assertFalse(again)

    def test_llms_gets_the_methodology_line_once(self):
        stub = f"## Pages\n- {bt.SITE}/stremio-profanity-filter.html \u2014 muting swearing in Stremio, step-by-step\n- x\n"
        out, changed, again = self.run_in_tmp("llms.txt", stub, bt.update_llms)
        self.assertEqual(out.count(f"{bt.SITE}/titles/methodology/"), 1)
        self.assertLess(out.index(f"{bt.SITE}/titles/ "), out.index(f"{bt.SITE}/titles/methodology/"))
        self.assertFalse(again)


if __name__ == "__main__":
    unittest.main()
