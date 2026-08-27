# Diversio HRIS Import Preview

A small Django web application that previews and validates an HRIS CSV before any employee or reporting relationship data is persisted.

## Features

- Upload an HRIS CSV from the browser
- Count total source rows
- Validate employee identity
- Detect duplicate employee IDs and emails
- Normalize whitespace and email addresses
- Resolve managers by employee ID or email
- Detect conflicting manager references
- Detect missing managers
- Identify root employees
- Calculate direct-report counts
- Detect reporting cycles
- Distinguish employees participating in cycles from employees merely reporting into a cycle
- Handle malformed uploads with clear errors
- Automated tests for important business rules

## Requirements

- Python 3.13+
- Django 6.1

## Setup

Clone or download the repository.

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install Django:

```bash
pip install django
```

## Run

Start the development server:

```bash
python manage.py runserver
```

Open:

http://127.0.0.1:8000/

Upload an HRIS CSV using the upload form.

## Tests

Run:

```bash
python manage.py test
```

The test suite covers:

- Duplicate employee identity validation
- Manager resolution using manager email
- Reporting cycle detection while excluding employees that only report into a cycle

## Architecture

The application separates web handling from HRIS business logic.

### `importer/views.py`

Handles the HTTP request, invokes the HRIS analysis functions, and passes the results to the template.

### `importer/services.py`

Contains the main CSV parsing, validation, manager resolution, direct-report calculation, and cycle-detection logic.

### `importer/templates/importer/upload.html`

Displays the import preview and validation results.

## Data Structures and Algorithms

Employee lookup is performed using dictionaries indexed by employee ID and normalized email.

Manager relationships are represented as:

```text
employee_id -> manager_id
```

Direct reports are calculated by reversing those relationships into:

```text
manager_id -> list of employee_ids
```

Reporting cycles are detected by following manager relationships while maintaining a current traversal path. If a manager is encountered that already exists in the current path, the employees from that point form a reporting cycle.

An employee that points into a cycle is not considered cyclic unless that employee is itself a member of the cycle.

## Complexity

For `n` employees:

- CSV parsing: O(n)
- Identity validation: O(n)
- Manager lookup: O(n) average time using dictionaries
- Direct-report calculation: O(n)
- Cycle detection: O(n)
- Overall expected time: O(n)
- Space: O(n)

The approach is designed to work with files approaching 100,000 employees without repeatedly scanning the entire employee list for manager lookups.

## Assumptions and Known Limitations

- Employee IDs are case-sensitive.
- Emails are normalized to lowercase.
- Surrounding whitespace is removed from values.
- Invalid employee identity rows are excluded from manager lookup and hierarchy analysis.
- An employee with a manager reference error remains an accepted employee but does not create a reporting relationship and is not considered a root.
- Database persistence is intentionally not implemented because it is not required for this exercise.
- Authentication and production deployment are outside the scope of this exercise.

## Sample Input

The application was tested against the supplied Diversio HRIS sample CSV.

## Time Spent

Approximately 90 minutes on implementation and testing, excluding the walkthrough recording.

## AI Usage

AI tools were used as a development aid for understanding Django structure, exploring implementation approaches, and reviewing edge cases.

I reviewed, tested, and modified the generated suggestions rather than using generated code without validation. In particular, I validated the manager-resolution and reporting-cycle behavior against custom cases and the supplied HRIS sample.

## Future Improvements

With more time, I would:

- Add more automated tests for malformed CSVs and manager-reference edge cases.
- Improve the presentation of hierarchy relationships.
- Add a larger test dataset for performance testing near 100,000 employees.
- Add stronger CSV validation for additional malformed input scenarios.