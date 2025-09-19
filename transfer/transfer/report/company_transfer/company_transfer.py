# Copyright (c) 2025, awad mohamed & atta almanan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data, chart = get_data_chart(filters=filters)
    return columns, data, None, chart


def get_data_chart(filters=None):
    data = []
    from_date = filters.pop("from_date", None)
    to_date = filters.pop("to_date", None)
    from_company = filters.pop("from_company", None)
    to_company = filters.pop("to_company", None)
    reciver_or_sender = filters.pop("reciver_or_sender", None)

    # build db filters
    db_filters = {}
    if from_company:
        db_filters["from_company"] = from_company
    if to_company:
        db_filters["to_company"] = to_company
    if from_date and to_date:
        db_filters["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        db_filters["posting_date"] = [">=", from_date]
    elif to_date:
        db_filters["posting_date"] = ["<=", to_date]
    if filters.get("status"):
        db_filters["status"] = filters.get("status")

    # fetch docs
    doc_list = frappe.get_all(
        "company transfer",
        filters=db_filters,
        fields=[
            "name",
            "from_company",
            "to_company",
            "status",
            "posting_date",
            "amount",
            "phone_number",
        ],
    )

    for doc in doc_list:
        d = {
            "ID": doc.name,
            "status": doc.status,
            "phone": doc.phone_number,
            "from_company": doc.from_company,
            "to_company": doc.to_company,
            "amount": doc.amount,
        }
        data.append(d)

    # decide grouping field for chart
    group_by_field = "from_company" if reciver_or_sender == "Sender" else "to_company"

    # build SQL WHERE clause dynamically
    conditions = []
    values = []

    if from_company:
        conditions.append("from_company=%s")
        values.append(from_company)
    if to_company:
        conditions.append("to_company=%s")
        values.append(to_company)
    if from_date and to_date:
        conditions.append("posting_date BETWEEN %s AND %s")
        values.extend([from_date, to_date])
    elif from_date:
        conditions.append("posting_date >= %s")
        values.append(from_date)
    elif to_date:
        conditions.append("posting_date <= %s")
        values.append(to_date)
    if filters.get("status"):
        conditions.append("status=%s")
        values.append(filters.get("status"))

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    totals = frappe.db.sql(
        f"""
        SELECT {group_by_field} as branch, COUNT(*) as total
        FROM `tabcompany transfer`
        {where_clause}
        GROUP BY {group_by_field}
        """,
        values,
        as_dict=True,
    )

    branches_list = [row.branch for row in totals]
    values_list = [row.total for row in totals]

    chart = {
        "data": {
            "labels": branches_list,
            "datasets": [
                {
                    "name": filters.get("status") or "Count",
                    "values": values_list,
                }
            ],
        },
        "type": "bar",
    }
    return data, chart


def get_columns():
    columns = [
        {
            "fieldname": "ID",
            "label": _("ID"),
            "fieldtype": "Link",
            "options": "company transfer",
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
        },
        {
            "fieldname": "phone",
            "label": _("Phone Number"),
            "fieldtype": "Data",
        },
        {
            "fieldname": "from_company",
            "label": _("Sender Branch"),
            "fieldtype": "Link",
            "options": "Branch",
        },
        {
            "fieldname": "to_company",
            "label": _("Reciver Branch"),
            "fieldtype": "Link",
            "options": "Branch",
        },
        {
            "fieldname": "amount",
            "label": _("amount"),
            "fieldtype": "Currency",
        },
    ]

    return columns
