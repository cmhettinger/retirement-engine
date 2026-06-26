"""Generate the blank Retirement Engine workbook template."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT_DIR / "resources" / "template.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="D9EAF7")
HEADER_FONT = Font(bold=True, size=12)
DEFAULT_FONT = Font(size=12)
DEFAULT_ROW_HEIGHT = 22
HEADER_ROW_HEIGHT = 24

CURRENCY_HEADERS = {
    "Annual",
    "Monthly",
    "Estimated Replacement Cost",
    "Current Balance",
    "Annual Contribution",
    "Employer Match",
    "Monthly Payment",
    "Annual Premium",
    "Coverage Amount",
}
PERCENT_HEADERS = {
    "Inflation Rate",
    "Expected Investment Return",
    "Estimated Tax Rate",
    "Interest Rate",
}
INTEGER_HEADERS = {
    "Current Age",
    "Planned Retirement Age",
    "Life Expectancy",
    "Social Security Claiming Age",
    "Planning Horizon Years",
    "Expected Useful Life",
    "Remaining Useful Life",
    "Next Replacement Year",
    "Payoff Year",
}


def yes_no_validation(field_name: str) -> DataValidation:
    validation = DataValidation(
        type="list",
        formula1='"Yes,No"',
        allow_blank=True,
    )
    validation.error = "Select Yes, No, or leave blank."
    validation.errorTitle = f"Invalid {field_name} value"
    validation.prompt = "Select Yes or No, or leave blank if not classified yet."
    validation.promptTitle = field_name
    return validation


def slug(value: str) -> str:
    text = value.lower()
    text = text.replace("'s", "s")
    text = text.replace("401(k)", "401k")
    text = text.replace("403(b)", "403b")
    text = text.replace("457", "457")
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def person_key(value: str) -> str:
    return value.lower().replace(" ", "")


def append_rows(sheet: Worksheet, headers: list[str], rows: Iterable[list[object]]) -> None:
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    format_sheet(sheet, headers)


def format_sheet(sheet: Worksheet, headers: list[str]) -> None:
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.sheet_format.defaultRowHeight = DEFAULT_ROW_HEIGHT

    for row in sheet.iter_rows():
        for cell in row:
            cell.font = DEFAULT_FONT

    sheet.row_dimensions[1].height = HEADER_ROW_HEIGHT

    for cell in sheet[1]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for index, header in enumerate(headers, start=1):
        column = get_column_letter(index)
        max_length = max(
            len(str(sheet.cell(row=row, column=index).value or ""))
            for row in range(1, sheet.max_row + 1)
        )
        sheet.column_dimensions[column].width = min(max(max_length + 2, 12), 34)

        if header in CURRENCY_HEADERS:
            number_format = '"$"#,##0'
        elif header in PERCENT_HEADERS:
            number_format = "0.0%"
        elif header in INTEGER_HEADERS:
            number_format = "0"
        else:
            number_format = None

        if number_format:
            for row in range(2, sheet.max_row + 1):
                sheet.cell(row=row, column=index).number_format = number_format


def format_assumption_values(sheet: Worksheet) -> None:
    for row in range(2, sheet.max_row + 1):
        assumption = str(sheet.cell(row=row, column=2).value or "")
        value_cell = sheet.cell(row=row, column=3)
        if assumption in PERCENT_HEADERS:
            value_cell.number_format = "0.0%"
        elif assumption in INTEGER_HEADERS:
            value_cell.number_format = "0"
        elif assumption in {"Desired Cash Reserve", "Desired Estate Value"}:
            value_cell.number_format = '"$"#,##0'


def add_yes_no_validation(sheet: Worksheet, column: str, field_name: str) -> None:
    validation = yes_no_validation(field_name)
    sheet.add_data_validation(validation)
    validation.add(f"{column}2:{column}{sheet.max_row}")


def build_assumptions() -> tuple[list[str], list[list[object]]]:
    headers = ["Person / Scope", "Assumption", "Value", "Notes", "ID"]
    rows: list[list[object]] = [
        ["System", "Workbook Version", "0.1.0", "", "system.workbook.version"]
    ]

    for person in ("Person 1", "Person 2"):
        key = person_key(person)
        rows.append([person, "Name", "", "", f"assumptions.{key}.name"])
        for assumption in (
            "Current Age",
            "Planned Retirement Age",
            "Life Expectancy",
            "Social Security Claiming Age",
        ):
            rows.append([person, assumption, "", "", f"assumptions.{key}.{slug(assumption)}"])

    for assumption in (
        "Planning Horizon Years",
        "Inflation Rate",
        "Expected Investment Return",
        "Estimated Tax Rate",
        "Desired Cash Reserve",
        "Desired Estate Value",
    ):
        rows.append(["Household", assumption, "", "", f"assumptions.household.{slug(assumption)}"])

    return headers, rows


def budget_rows() -> tuple[list[str], list[list[object]]]:
    headers = ["Must Pay", "Category", "Item", "Annual", "Monthly", "Notes", "ID"]
    categories = {
        "Housing": [
            "Mortgage / Rent",
            "Property Taxes",
            "Homeowners / Renters Insurance",
            "HOA / Condo Fees",
            "Home Maintenance",
            "Lawn Care",
            "Snow Removal",
            "Pest Control",
            "House Cleaning",
            "Handyman Services",
            "Window / Gutter Cleaning",
            "Tree Removal",
            "Household Supplies",
        ],
        "Utilities": [
            "Electricity",
            "Natural Gas / Propane / Heating Oil",
            "Water",
            "Sewer",
            "Trash / Recycling",
            "Generator Fuel / Backup Power",
        ],
        "Food": ["Groceries", "Restaurants", "Coffee / Snacks", "Alcohol", "Meal Delivery"],
        "Healthcare": [
            "Health Insurance Premiums",
            "Medicare Premiums",
            "Medicare Supplement",
            "Dental Insurance",
            "Vision Insurance",
            "Prescription Medications",
            "Over-the-Counter Medications",
            "Doctor Visits",
            "Specialists",
            "Dental Care",
            "Vision Care",
            "Hearing Care",
            "Medical Equipment",
            "Long-Term Care Insurance",
            "Out-of-Pocket Medical",
            "Gym / Wellness",
        ],
        "Insurance": [
            "Life Insurance",
            "Umbrella Liability",
            "Identity Theft Protection",
            "Pet Insurance",
            "Flood Insurance",
            "Earthquake Insurance",
            "RV / Boat / Motorcycle Insurance",
        ],
        "Taxes": [
            "Federal Income Tax",
            "State Income Tax",
            "Local Taxes",
            "Capital Gains Tax",
            "Estimated Tax Payments",
        ],
        "Transportation": [
            "Vehicle Payments",
            "Fuel",
            "Auto Insurance",
            "Registration / Inspection",
            "Driver's License Renewal",
            "Vehicle Property Tax",
            "Maintenance",
            "Tires",
            "Repairs",
            "Parking",
            "Tolls",
            "Public Transportation",
            "Ride Sharing",
        ],
        "Communications": [
            "Internet",
            "Mobile Phones",
            "Home Phone",
            "Cable / Satellite TV",
            "Streaming Services",
            "Cloud Storage",
        ],
        "Personal": [
            "Clothing",
            "Shoes",
            "Haircuts",
            "Personal Care",
            "Toiletries",
            "Laundry / Dry Cleaning",
        ],
        "Family": [
            "Gifts",
            "Holidays",
            "Grandchildren",
            "Charitable Giving",
            "Family Support",
            "Weddings / Funerals",
        ],
        "Pets": ["Pet Food", "Veterinary Care", "Grooming", "Boarding", "Medications"],
        "Financial": [
            "Investment Management Fees",
            "Financial Advisor",
            "Tax Preparation",
            "Tax Software",
            "Brokerage / Custodial Fees",
            "Banking Fees",
            "Safe Deposit Box",
        ],
        "Debt": [
            "Credit Cards",
            "Personal Loans",
            "Home Equity Loan",
            "Student Loans",
            "Other Debt",
        ],
        "Legal": [
            "Estate Planning",
            "Attorney / Legal Services",
            "Trust & Will Updates",
            "Notary / Filing Fees",
            "Document Storage",
        ],
        "Memberships": [
            "Gym Membership",
            "Warehouse Clubs",
            "Professional Organizations",
            "Clubs / Associations",
            "Software Subscriptions",
        ],
        "Recreation": [
            "Travel",
            "Vacations",
            "Hotels",
            "Cruises",
            "Hobbies",
            "Sporting Events",
            "Concerts",
            "Clubs",
            "Golf",
            "Fishing / Hunting",
            "Books",
            "Movies",
            "Entertainment Subscriptions",
            "Education / Classes",
            "National / State Park Passes",
        ],
        "Replacement Reserve": ["Annual Replacement Reserve Contribution"],
        "Other": [
            "Amazon / General Shopping",
            "Office Supplies",
            "Postage / Shipping",
            "Miscellaneous",
            "Contingency",
        ],
    }
    rows = [
        ["", category, item, "", "", "", f"budget.{slug(category)}.{slug(item)}"]
        for category, items in categories.items()
        for item in items
    ]
    return headers, rows


def reserve_rows() -> tuple[list[str], list[list[object]]]:
    headers = [
        "Reserve Item",
        "Estimated Replacement Cost",
        "Expected Useful Life",
        "Current Age",
        "Remaining Useful Life",
        "Next Replacement Year",
        "Notes",
        "ID",
    ]
    items = [
        "Emergency Fund Replenishment",
        "Roof",
        "HVAC System",
        "Water Heater",
        "Plumbing Repairs",
        "Electrical Repairs",
        "Appliance Replacement",
        "Flooring / Carpet",
        "Exterior Painting",
        "Remodeling / Renovation",
        "Windows / Doors",
        "Driveway / Walkway",
        "Deck / Patio",
        "Landscaping",
        "Furniture",
        "Mattress Replacement",
        "Vehicle Replacement",
        "Vehicle Major Repairs",
        "Computer Replacement",
        "Phone Replacement",
        "Tablet Replacement",
        "Television / Electronics",
        "Camera Equipment",
        "Travel Fund",
        "Medical Contingency",
        "Long-Term Care Reserve",
        "Family Assistance Reserve",
        "Pet Medical Reserve",
        "Other",
    ]
    rows = [[item, "", "", "", "", "", "", f"reserve.{slug(item)}"] for item in items]
    return headers, rows


def income_rows() -> tuple[list[str], list[list[object]]]:
    headers = ["Owner", "Income Source", "Annual", "Monthly", "Taxable", "Notes", "ID"]
    items = [
        ("Person 1", "Social Security"),
        ("Person 2", "Social Security"),
        ("Person 1", "Pension"),
        ("Person 2", "Pension"),
        ("Household", "Traditional IRA Withdrawals"),
        ("Household", "Roth IRA Withdrawals"),
        ("Household", "401(k) Withdrawals"),
        ("Household", "403(b) / 457 Withdrawals"),
        ("Household", "Taxable Brokerage Withdrawals"),
        ("Household", "Dividends"),
        ("Household", "Interest Income"),
        ("Household", "Rental Income"),
        ("Household", "Business Income"),
        ("Household", "Annuities"),
        ("Household", "Part-Time Employment"),
        ("Household", "VA Benefits"),
        ("Household", "Disability Benefits"),
        ("Household", "Other Income"),
    ]
    rows = [
        [owner, source, "", "", "", "", f"income.{person_key(owner)}.{slug(source)}"]
        for owner, source in items
    ]
    return headers, rows


def asset_rows() -> tuple[list[str], list[list[object]]]:
    headers = [
        "Owner",
        "Account Type",
        "Institution",
        "Current Balance",
        "Annual Contribution",
        "Employer Match",
        "Tax Treatment",
        "Notes",
        "ID",
    ]
    items = [
        ("Person 1", "401(k)"),
        ("Person 1", "Traditional IRA"),
        ("Person 1", "Roth IRA"),
        ("Person 1", "HSA"),
        ("Person 2", "401(k)"),
        ("Person 2", "Traditional IRA"),
        ("Person 2", "Roth IRA"),
        ("Person 2", "HSA"),
        ("Household", "Taxable Brokerage"),
        ("Household", "Cash / Savings"),
        ("Household", "CDs / Money Market"),
        ("Household", "Real Estate"),
        ("Household", "Other Assets"),
    ]
    rows = [
        [owner, account, "", "", "", "", "", "", f"asset.{person_key(owner)}.{slug(account)}"]
        for owner, account in items
    ]
    return headers, rows


def liability_rows() -> tuple[list[str], list[list[object]]]:
    headers = [
        "Owner",
        "Liability Type",
        "Lender",
        "Current Balance",
        "Interest Rate",
        "Monthly Payment",
        "Payoff Year",
        "Notes",
        "ID",
    ]
    items = [
        ("Household", "Mortgage"),
        ("Household", "Home Equity Loan"),
        ("Household", "Vehicle Loan"),
        ("Household", "Credit Card Debt"),
        ("Household", "Personal Loan"),
        ("Household", "Student Loan"),
        ("Household", "Medical Debt"),
        ("Household", "Other Liability"),
    ]
    rows = [
        [
            owner,
            liability,
            "",
            "",
            "",
            "",
            "",
            "",
            f"liability.{person_key(owner)}.{slug(liability)}",
        ]
        for owner, liability in items
    ]
    return headers, rows


def insurance_rows() -> tuple[list[str], list[list[object]]]:
    headers = [
        "Owner",
        "Policy Type",
        "Provider",
        "Annual Premium",
        "Coverage Amount",
        "Beneficiary",
        "Notes",
        "ID",
    ]
    items = [
        ("Person 1", "Life Insurance"),
        ("Person 2", "Life Insurance"),
        ("Person 1", "Disability Insurance"),
        ("Person 2", "Disability Insurance"),
        ("Person 1", "Long-Term Care Insurance"),
        ("Person 2", "Long-Term Care Insurance"),
        ("Household", "Health Insurance"),
        ("Household", "Dental Insurance"),
        ("Household", "Vision Insurance"),
        ("Household", "Homeowners Insurance"),
        ("Household", "Auto Insurance"),
        ("Household", "Umbrella Insurance"),
    ]
    rows = [
        [owner, policy, "", "", "", "", "", f"insurance.{person_key(owner)}.{slug(policy)}"]
        for owner, policy in items
    ]
    return headers, rows


def build_workbook() -> Workbook:
    workbook = Workbook()
    workbook.remove(workbook.active)

    sheets = [
        ("Assumptions", build_assumptions()),
        ("Budget", budget_rows()),
        ("Reserves", reserve_rows()),
        ("Income", income_rows()),
        ("Assets", asset_rows()),
        ("Liabilities", liability_rows()),
        ("Insurance", insurance_rows()),
    ]

    for name, (headers, rows) in sheets:
        sheet = workbook.create_sheet(name)
        append_rows(sheet, headers, rows)
        if name == "Assumptions":
            format_assumption_values(sheet)
        elif name == "Budget":
            add_yes_no_validation(sheet, "A", "Must Pay")
        elif name == "Income":
            add_yes_no_validation(sheet, "E", "Taxable")

    workbook.active = 0
    return workbook


def main() -> None:
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    workbook = build_workbook()
    workbook.save(TEMPLATE_PATH)
    print(f"Generated {TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
