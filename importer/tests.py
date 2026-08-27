

# Create your tests here.
from django.test import SimpleTestCase

from .services import (
    validate_employee_identity,
    resolve_managers,
    find_reporting_cycles,
)


class HRISValidationTests(SimpleTestCase):

    def test_duplicate_employee_id_invalidates_all_duplicate_rows(self):
        rows = [
            {
                "employee_id": "E001",
                "employee_name": "Alice",
                "email": "alice@example.com",
                "manager_id": "",
                "manager_email": "",
                "department": "Engineering",
                "_source_row": 2,
            },
            {
                "employee_id": "E001",
                "employee_name": "Bob",
                "email": "bob@example.com",
                "manager_id": "",
                "manager_email": "",
                "department": "Engineering",
                "_source_row": 3,
            },
        ]

        accepted, errors = validate_employee_identity(rows)

        self.assertEqual(accepted, [])
        self.assertEqual(len(errors), 2)


class HRISManagerTests(SimpleTestCase):

    def test_manager_email_resolves_correctly(self):
        rows = [
            {
                "employee_id": "E001",
                "employee_name": "Alice",
                "email": "alice@example.com",
                "manager_id": "",
                "manager_email": "",
                "department": "Engineering",
                "_source_row": 2,
            },
            {
                "employee_id": "E002",
                "employee_name": "Bob",
                "email": "bob@example.com",
                "manager_id": "",
                "manager_email": "alice@example.com",
                "department": "Engineering",
                "_source_row": 3,
            },
        ]

        relationships, roots, errors = resolve_managers(rows)

        self.assertEqual(
            relationships,
            {"E002": "E001"}
        )

        self.assertEqual(
            [employee["employee_id"] for employee in roots],
            ["E001"]
        )

        self.assertEqual(errors, [])


class HRISCycleTests(SimpleTestCase):

    def test_employee_reporting_into_cycle_is_not_cyclic(self):
        relationships = {
            "E001": "E003",
            "E002": "E001",
            "E003": "E002",
            "E004": "E001",
        }

        cycles = find_reporting_cycles(relationships)

        cyclic_employees = {
            employee_id
            for cycle in cycles
            for employee_id in cycle
        }

        self.assertEqual(
            cyclic_employees,
            {"E001", "E002", "E003"}
        )

        self.assertNotIn("E004", cyclic_employees)