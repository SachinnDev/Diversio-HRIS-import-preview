from django.shortcuts import render

from .services import (
    parse_csv,
    validate_employee_identity,
    build_employee_lookups,
    resolve_managers,
    calculate_direct_reports,
    find_reporting_cycles,
)


def upload_csv(request):
    context = {}

    if request.method == "POST":
        uploaded_file = request.FILES.get("csv_file")

        if uploaded_file:
            try:
                # Step 1: Parse CSV
                rows = parse_csv(uploaded_file)

                # Step 2: Validate employee identity
                accepted_rows, identity_errors = validate_employee_identity(rows)

                # Step 3: Build employee lookup dictionaries
                employees_by_id, employees_by_email = build_employee_lookups(
                    accepted_rows
                )

                # Step 4: Resolve manager relationships
                relationships, roots, manager_errors = resolve_managers(
                    accepted_rows
                )

                # Step 5: Calculate managers and direct reports
                managers = calculate_direct_reports(
                    relationships,
                    employees_by_id
                )

                # Step 6: Find reporting cycles
                cycles = find_reporting_cycles(relationships)
                cycle_details = []

                for cycle in cycles:
                 cycle_details.append([
                    employees_by_id[employee_id]
                     for employee_id in cycle
                 ])

                # Combine all errors
                all_errors = identity_errors + manager_errors

                context = {
                    "total_rows": len(rows),
                    "accepted_employees": accepted_rows,
                    "errors": all_errors,
                    "roots": roots,
                    "managers": managers,
                    "cycles": cycle_details,
                }

            except (UnicodeDecodeError, ValueError) as error:
                context["upload_error"] = str(error)

    return render(request, "importer/upload.html", context)