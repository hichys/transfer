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
    from_branch = filters.pop("from_branch", None)
    to_branch = filters.pop("to_branch", None)
    reciver_or_sender = filters.pop("reciver_or_sender", None)

    # build db filters
    db_filters = {}
    if from_branch:
        db_filters["from_branch"] = from_branch
    if to_branch:
        db_filters["to_branch"] = to_branch
    if from_date and to_date:
        db_filters["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        db_filters["posting_date"] = [">=", from_date]
    elif to_date:
        db_filters["posting_date"] = ["<=", to_date]
    if filters.get("workflow_state"):
        db_filters["workflow_state"] = filters.get("workflow_state")

    # fetch docs
    doc_list = frappe.get_all(
        "transfer between branches",
        filters=db_filters,
        fields=[
            "name",
            "from_branch",
            "to_branch",
            "workflow_state",
            "posting_date",
            "amount",
            "phone_number",
        ],
    )

    for doc in doc_list:
        d = {
            "ID": doc.name,
            "status": doc.workflow_state,
            "phone": doc.phone_number,
            "from_branch": doc.from_branch,
            "to_branch": doc.to_branch,
            "amount": doc.amount,
        }
        data.append(d)

    # decide grouping field for chart
    group_by_field = "from_branch" if reciver_or_sender == "Sender" else "to_branch"

    # build SQL WHERE clause dynamically
    conditions = []
    values = []

    if from_branch:
        conditions.append("from_branch=%s")
        values.append(from_branch)
    if to_branch:
        conditions.append("to_branch=%s")
        values.append(to_branch)
    if from_date and to_date:
        conditions.append("posting_date BETWEEN %s AND %s")
        values.extend([from_date, to_date])
    elif from_date:
        conditions.append("posting_date >= %s")
        values.append(from_date)
    elif to_date:
        conditions.append("posting_date <= %s")
        values.append(to_date)
    if filters.get("workflow_state"):
        conditions.append("workflow_state=%s")
        values.append(filters.get("workflow_state"))

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    totals = frappe.db.sql(
        f"""
        SELECT {group_by_field} as branch, COUNT(*) as total
        FROM `tabtransfer between branches`
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
                    "name": filters.get("workflow_state") or "Count",
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
            "options": "transfer between branches",
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
            "fieldname": "from_branch",
            "label": _("Sender Branch"),
            "fieldtype": "Link",
            "options": "Branch",
        },
        {
            "fieldname": "to_branch",
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
