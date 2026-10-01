from hashlib import sha256
from unittest import TestCase

from src.domain.enums.app_mode import AppMode
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy


class TestAuditPayloadPolicy(TestCase):
    def test_debug_returns_empty_payload_unchanged(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.DEBUG)

        result = policy.apply("")

        self.assertEqual(result, "")

    def test_debug_returns_multiline_and_unicode_payload_unchanged(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.DEBUG)
        payload = "Línea 1: El ñandú veloz.\nLínea 2: ¿Detecta errores? 🚀"

        result = policy.apply(payload)

        self.assertEqual(result, payload)

    def test_debug_returns_very_long_payload_unchanged(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.DEBUG)
        payload = "x" * 100000

        result = policy.apply(payload)

        self.assertEqual(result, payload)

    def test_prod_returns_expected_marker_with_exact_char_count_and_sha256(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        payload = "Este es un manuscrito confidencial."
        expected_hash = sha256(payload.encode("utf-8")).hexdigest()
        expected_length = len(payload)
        expected_marker = f"[REDACTED chars={expected_length} sha256={expected_hash}]"

        result = policy.apply(payload)

        self.assertEqual(result, expected_marker)

    def test_prod_marker_contains_no_fragment_of_original_text(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        author_private_text = "PrivateAuthorManuscriptContent"
        payload = f"Capítulo 1: {author_private_text} continúa la historia."

        result = policy.apply(payload)

        self.assertNotIn(author_private_text, result)
        self.assertNotIn("Capítulo", result)
        self.assertNotIn("continúa", result)

    def test_prod_is_deterministic_for_same_input(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        payload = "Texto idéntico para verificación de determinismo."

        first_result = policy.apply(payload)
        second_result = policy.apply(payload)

        self.assertEqual(first_result, second_result)

    def test_prod_yields_different_markers_for_different_inputs(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        first_payload = "Texto A"
        second_payload = "Texto B"

        first_result = policy.apply(first_payload)
        second_result = policy.apply(second_payload)

        self.assertNotEqual(first_result, second_result)

    def test_prod_counts_characters_not_bytes_for_unicode(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        payload = "ñandú"
        self.assertEqual(len(payload), 5)
        self.assertEqual(len(payload.encode("utf-8")), 7)
        expected_hash = sha256(payload.encode("utf-8")).hexdigest()
        expected_marker = f"[REDACTED chars=5 sha256={expected_hash}]"

        result = policy.apply(payload)

        self.assertEqual(result, expected_marker)

    def test_prod_empty_payload_gives_chars_zero_and_empty_sha256(self):
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        empty_hash = sha256("".encode("utf-8")).hexdigest()
        expected_marker = f"[REDACTED chars=0 sha256={empty_hash}]"

        result = policy.apply("")

        self.assertEqual(result, expected_marker)
