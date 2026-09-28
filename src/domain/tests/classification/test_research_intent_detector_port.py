from unittest import TestCase

from src.domain.classification.research_intent_detector_port import (
    ResearchIntentDetectorPort,
)
from src.domain.tests.classification.fake_research_intent_detector_port import (
    FakeResearchIntentDetectorPort,
)


class TestResearchIntentDetectorPort(TestCase):
    def test_direct_instantiation_raises_type_error(self):
        with self.assertRaises(TypeError):
            ResearchIntentDetectorPort()  # type: ignore[abstract]

    def test_fake_is_instance_of_port(self):
        fake = FakeResearchIntentDetectorPort()
        self.assertIsInstance(fake, ResearchIntentDetectorPort)

    def test_fake_detect_returns_configured_signals(self):
        fake = FakeResearchIntentDetectorPort(signals=(True, False, True))
        result = fake.detect(text_sample="Sample text", title="Sample Title")
        self.assertEqual(result, (True, False, True))

    def test_fake_detect_returns_default_signals_when_unconfigured(self):
        fake = FakeResearchIntentDetectorPort()
        result = fake.detect(text_sample="Sample text", title=None)
        self.assertEqual(result, (False, False, False))

    def test_fake_raises_configured_error(self):
        fake = FakeResearchIntentDetectorPort(error=ValueError("Detection error"))
        with self.assertRaises(ValueError):
            fake.detect(text_sample="Sample text", title=None)
