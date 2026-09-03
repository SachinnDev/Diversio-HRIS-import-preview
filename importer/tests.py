from django.test import SimpleTestCase

from .services import (
    validate_employee_identity,
    build_employee_lookups,
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

    def test_duplicate_email_invalidates_all_duplicate_rows(self):
        rows = [
        {
            "employee_id": "E001",
            "employee_name": "Alice",
            "email": "same@example.com",
            "manager_id": "",
            "manager_email": "",
            "department": "Engineering",
            "_source_row": 2,
        },
        {
            "employee_id": "E002",
            "employee_name": "Bob",
            "email": "same@example.com",
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

        employees_by_id, employees_by_email = build_employee_lookups(rows)

        relationships, roots, errors = resolve_managers(
            rows,
            employees_by_id,
            employees_by_email,
        )

        self.assertEqual(
            relationships,
            {"E002": "E001"}
        )

        self.assertEqual(
            [employee["employee_id"] for employee in roots],
            ["E001"]
        )

        self.assertEqual(errors, [])

    def test_missing_manager_is_reported_as_error(self):
        rows = [
            {
                "employee_id": "E001",
                "employee_name": "Alice",
                "email": "alice@example.com",
                "manager_id": "E999",
                "manager_email": "",
                "department": "Engineering",
                "_source_row": 2,
            }
        ]

        employees_by_id, employees_by_email = build_employee_lookups(rows)

        relationships, roots, errors = resolve_managers(
            rows,
            employees_by_id,
            employees_by_email,
        )

        self.assertEqual(relationships, {})
        self.assertEqual(roots, [])
        self.assertEqual(len(errors), 1)
        self.assertIn(
            "could not be found",
            errors[0]["message"]
        )
    def test_conflicting_manager_references_are_reported(self):
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
            "manager_email": "",
            "department": "Engineering",
            "_source_row": 3,
        },
        {
            "employee_id": "E003",
            "employee_name": "Charlie",
            "email": "charlie@example.com",
            "manager_id": "E001",
            "manager_email": "bob@example.com",
            "department": "Engineering",
            "_source_row": 4,
        },
    ]

        employees_by_id, employees_by_email = build_employee_lookups(rows)

        relationships, roots, errors = resolve_managers(
        rows,
        employees_by_id,
        employees_by_email,
    )

        self.assertNotIn("E003", relationships)
        self.assertEqual(len(errors), 1)
        self.assertIn(
        "different employees",
        errors[0]["message"]
    )    


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