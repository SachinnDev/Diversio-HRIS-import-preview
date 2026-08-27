import csv
import io


EXPECTED_HEADERS = {
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
}


def parse_csv(uploaded_file):
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError(
            "The uploaded file is not valid UTF-8."
        )

    if not text.strip():
        raise ValueError(
            "The uploaded CSV file is empty."
        )

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError(
            "The CSV file has no header row."
        )

    # Normalize header names.
    normalized_headers = [
        header.strip()
        for header in reader.fieldnames
        if header is not None
    ]

    expected_headers = EXPECTED_HEADERS

    actual_headers = set(normalized_headers)

    missing = expected_headers - actual_headers
    extra = actual_headers - expected_headers
    duplicate_headers = {
    header
    for header in normalized_headers
    if normalized_headers.count(header) > 1
    }

    if (
    missing
    or extra
    or duplicate_headers
    or len(normalized_headers) != len(expected_headers)
    ):
     message = "Invalid CSV headers."

    if missing:
        message += f" Missing: {', '.join(sorted(missing))}."

    if extra:
        message += f" Unexpected: {', '.join(sorted(extra))}."

    if duplicate_headers:
        message += (
            f" Duplicate headers: {', '.join(sorted(duplicate_headers))}."
        )

    raise ValueError(message)

    rows = []

    for row_number, row in enumerate(reader, start=2):

        normalized_row = {}

        for key, value in row.items():

            if key is None:
                continue

            normalized_key = key.strip()

            value = value.strip() if value is not None else ""

            if normalized_key in {"email", "manager_email"}:
                value = value.lower()

            normalized_row[normalized_key] = value

        normalized_row["_source_row"] = row_number

        rows.append(normalized_row)

    return rows


def validate_employee_identity(rows):
    errors = []

    employee_id_rows = {}
    email_rows = {}

    # First pass: find missing values and remember
    # which rows use each employee ID and email.
    for row in rows:
        row_number = row["_source_row"]
        employee_id = row["employee_id"]
        email = row["email"]

        if not employee_id:
            errors.append({
                "row": row_number,
                "message": "employee_id is required."
            })

        if not email:
            errors.append({
                "row": row_number,
                "message": "email is required."
            })

        if employee_id:
            employee_id_rows.setdefault(employee_id, []).append(row_number)

        if email:
            email_rows.setdefault(email, []).append(row_number)

    # Find duplicate employee IDs.
    duplicate_ids = {
        employee_id
        for employee_id, row_numbers in employee_id_rows.items()
        if len(row_numbers) > 1
    }

    # Find duplicate emails.
    duplicate_emails = {
        email
        for email, row_numbers in email_rows.items()
        if len(row_numbers) > 1
    }

    # Add errors for duplicate IDs.
    for employee_id in duplicate_ids:
        for row_number in employee_id_rows[employee_id]:
            errors.append({
                "row": row_number,
                "message": f"Duplicate employee_id: {employee_id}."
            })

    # Add errors for duplicate emails.
    for email in duplicate_emails:
        for row_number in email_rows[email]:
            errors.append({
                "row": row_number,
                "message": f"Duplicate email: {email}."
            })

    # Any row with an identity error is invalid.
    invalid_rows = {
        error["row"]
        for error in errors
    }

    accepted_rows = [
        row
        for row in rows
        if row["_source_row"] not in invalid_rows
    ]

    return accepted_rows, errors

def build_employee_lookups(accepted_rows):
    employees_by_id = {}
    employees_by_email = {}

    for employee in accepted_rows:
        employees_by_id[employee["employee_id"]] = employee
        employees_by_email[employee["email"]] = employee

    return employees_by_id, employees_by_email

def resolve_managers(accepted_rows):
    employees_by_id, employees_by_email = build_employee_lookups(
        accepted_rows
    )

    relationships = {}
    roots = []
    errors = []

    for employee in accepted_rows:
        row_number = employee["_source_row"]
        employee_id = employee["employee_id"]

        manager_id = employee["manager_id"]
        manager_email = employee["manager_email"]

        # Case 1: No manager information.
        if not manager_id and not manager_email:
            roots.append(employee)
            continue

        manager_by_id = None
        manager_by_email = None

        # Find manager using employee ID.
        if manager_id:
            manager_by_id = employees_by_id.get(manager_id)

        # Find manager using email.
        if manager_email:
            manager_by_email = employees_by_email.get(manager_email)

        # Case 2: manager_id supplied but manager not found.
        if manager_id and not manager_by_id:
            errors.append({
                "row": row_number,
                "message": f"Manager employee_id '{manager_id}' could not be found."
            })
            continue

        # Case 3: manager_email supplied but manager not found.
        if manager_email and not manager_by_email:
            errors.append({
                "row": row_number,
                "message": f"Manager email '{manager_email}' could not be found."
            })
            continue

        # Case 4: both supplied but they identify different employees.
        if manager_by_id and manager_by_email:
            if manager_by_id["employee_id"] != manager_by_email["employee_id"]:
                errors.append({
                    "row": row_number,
                    "message": "manager_id and manager_email refer to different employees."
                })
                continue

        # Determine the actual manager.
        manager = manager_by_id or manager_by_email

        # Employee cannot manage themselves.
        if manager["employee_id"] == employee_id:
            errors.append({
                "row": row_number,
                "message": "An employee cannot manage themselves."
            })
            continue

        relationships[employee_id] = manager["employee_id"]

    return relationships, roots, errors

def calculate_direct_reports(relationships, employees_by_id):
    direct_reports = {}

    for employee_id, manager_id in relationships.items():
        if manager_id not in direct_reports:
            direct_reports[manager_id] = []

        direct_reports[manager_id].append(employee_id)

    managers = []

    for manager_id, report_ids in direct_reports.items():
        managers.append({
            "employee": employees_by_id[manager_id],
            "direct_report_count": len(report_ids),
            "direct_reports": [
                employees_by_id[employee_id]
                for employee_id in report_ids
            ],
        })

    return managers

def find_reporting_cycles(relationships):
    cycles = []
    visited = set()

    for employee_id in relationships:
        if employee_id in visited:
            continue

        current_path = []
        path_index = {}

        current = employee_id

        while current in relationships and current not in visited:
            if current in path_index:
                cycle_start = path_index[current]
                cycle_members = current_path[cycle_start:]

                cycles.append(cycle_members)
                break

            path_index[current] = len(current_path)
            current_path.append(current)

            current = relationships[current]

        # Everything we traversed is now globally visited.
        visited.update(current_path)

    return cycles