from unittest import TestCase

from src.domain.enums.execution_status import ExecutionStatus


class TestExecutionStatus(TestCase):
    def test_members_and_values(self):
        self.assertEqual(ExecutionStatus.RUNNING.value, "running")
        self.assertEqual(ExecutionStatus.SUCCESS.value, "success")
        self.assertEqual(ExecutionStatus.ERROR.value, "error")

    def test_lookup_by_value(self):
        self.assertIs(ExecutionStatus("running"), ExecutionStatus.RUNNING)
        self.assertIs(ExecutionStatus("success"), ExecutionStatus.SUCCESS)
        self.assertIs(ExecutionStatus("error"), ExecutionStatus.ERROR)

    def test_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            ExecutionStatus("invalid")

    def test_member_count(self):
        self.assertEqual(len(ExecutionStatus), 3)

    def test_importable_independently(self):
        self.assertIsNotNone(ExecutionStatus)
