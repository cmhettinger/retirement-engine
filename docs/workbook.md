# Workbook

The Retirement Engine workbook is the human-editable financial model for a household.
It is designed for humans first: people should be able to review, share, and update
their planning facts and assumptions without needing to understand Python or the
engine internals.

The workbook should stay simple. It is intended for structured data entry, not for
business logic, financial calculations, projections, simulations, or reporting logic.
Those responsibilities belong in the Python engine.

Users may enter either annual or monthly amounts where both columns are available,
such as on the `Budget` and `Income` sheets. Some costs and income sources are
naturally annual, while others are naturally monthly. Python will later normalize
those values and calculate totals rather than forcing formulas into the editable
workbook.

The template does not include total rows inside the main data-entry sheets. This
keeps the sheets easy to extend by adding rows. Future totals should live in Python
outputs, reports, or separate summary sheets rather than in fragile embedded ranges.

Each worksheet includes an `ID` column with stable snake/dot-style identifiers. These
IDs are intended to become the durable link between workbook rows and the Python
engine, so they should not be changed casually after personal workbooks exist.

Person names belong on the `Assumptions` sheet in the `Person 1 / Name` and
`Person 2 / Name` rows. Reports should use those values for display labels rather
than hardcoding `Person 1` or `Person 2`.

The `Budget` sheet's `Must Pay` column is intentionally constrained to `Yes`, `No`,
or blank. Blank means the row has not been classified yet.

The `Income` sheet's `Taxable` column follows the same pattern: `Yes`, `No`, or
blank. The workbook uses human-friendly values instead of programming booleans.

Users may add additional rows to model real household complexity. For example, the
`Assets` sheet can contain multiple 401(k), IRA, brokerage, savings, or real estate
accounts. Each row should represent one account, and each added row should have a
unique stable ID such as `asset.person1.401k.current_employer` or
`asset.person1.401k.prior_employer`.

`resources/template.xlsx` is the checked-in blank workbook template. It is generated
by `tools/generate_template.py` and can be rebuilt with:

```sh
make template
```

Populated personal workbooks may contain private household financial data and should
not be committed. Other `.xlsx` files are ignored by Git; the checked-in blank
template is `resources/template.xlsx`.

The workbook schema version is stored in the workbook itself as
`system.workbook.version`. This is separate from the application version in the root
`VERSION` file. `env/config.yml` should reference the supported workbook schema
version, not the application version.
