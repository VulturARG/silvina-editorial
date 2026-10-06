from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from unittest import TestCase

from src.domain.tests.quality.feedback_structure_parser_builder_for_test import (
    FeedbackStructureParserBuilderForTest,
)


class TestFeedbackStructureParserConcurrency(TestCase):
    def test_parser_and_injected_collaborators_remain_stateless_and_deterministic_across_parses(
        self,
    ) -> None:
        parser = FeedbackStructureParserBuilderForTest().build()

        initial_collaborators_snapshots = {
            name: deepcopy(vars(collaborator))
            for name, collaborator in vars(parser).items()
            if not name.startswith("_handlers")
        }

        lead_in_input = [
            "Introducción explicativa.",
            "El texto presenta tres lineas explicativas:",
            "- Primera línea",
            "- Segunda línea con detalle:",
            "  - Sub-viñeta anidada",
            "- Tercera línea",
        ]
        nested_bullets_input = [
            "### Fortalezas",
            "- Elemento principal uno",
            "  - Sub-elemento alfa",
            "  - Sub-elemento beta",
            "- Elemento principal dos",
        ]
        numbered_items_input = [
            "### Plan de trabajo",
            "1. Primer paso analítico",
            "2. Segundo paso analítico",
            "### Segunda etapa",
            "1. Tercer paso analítico",
        ]

        result_a_first = parser.parse(lead_in_input)
        result_b_first = parser.parse(nested_bullets_input)
        result_c_first = parser.parse(numbered_items_input)

        result_a_second = parser.parse(lead_in_input)
        result_b_second = parser.parse(nested_bullets_input)
        result_c_second = parser.parse(numbered_items_input)

        self.assertEqual(result_a_first, result_a_second)
        self.assertEqual(result_b_first, result_b_second)
        self.assertEqual(result_c_first, result_c_second)

        interleaved_a = parser.parse(lead_in_input)
        self.assertEqual(interleaved_a, result_a_first)

        for name, initial_snapshot in initial_collaborators_snapshots.items():
            current_snapshot = vars(getattr(parser, name))
            self.assertEqual(
                current_snapshot,
                initial_snapshot,
                f"Collaborator {name} state was mutated during parse() execution",
            )

    def test_concurrent_parses_in_thread_pool_produce_identical_results_to_sequential_run(
        self,
    ) -> None:
        parser = FeedbackStructureParserBuilderForTest().build()

        fixtures = [
            [
                "Introducción explicativa.",
                "El texto presenta tres lineas explicativas:",
                "- Primera línea",
                "- Segunda línea con detalle:",
                "  - Sub-viñeta anidada",
                "- Tercera línea",
            ],
            [
                "### Fortalezas",
                "- Elemento principal uno",
                "  - Sub-elemento alfa",
                "  - Sub-elemento beta",
                "- Elemento principal dos",
            ],
            [
                "### Plan de trabajo",
                "1. Primer paso analítico",
                "2. Segundo paso analítico",
                "### Segunda etapa",
                "1. Tercer paso analítico",
            ],
        ]

        expected_results = [parser.parse(fixture) for fixture in fixtures]

        tasks = []
        for index in range(96):
            fixture_index = index % len(fixtures)
            tasks.append((fixture_index, fixtures[fixture_index]))

        def run_parse(task_data):
            fixture_idx, lines = task_data
            return fixture_idx, parser.parse(lines)

        with ThreadPoolExecutor(max_workers=8) as executor:
            completed_results = list(executor.map(run_parse, tasks))

        for fixture_idx, concurrent_result in completed_results:
            self.assertEqual(concurrent_result, expected_results[fixture_idx])
