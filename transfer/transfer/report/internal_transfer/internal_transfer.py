import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data, chart, summary = get_data_chart(filters or {})
    return columns, data, None, chart, summary


def get_data_chart(filters=None):
    data = []
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    status = filters.get("status")
    reciver_or_sender = filters.get("reciver_or_sender")
    transfer_type = filters.get("type")

    db_filters = {}
    if transfer_type == "من فرع الي شركة":
        db_filters["from_type"] = "Branch"
        db_filters["to_type"] = "Customer"

        if filters.get("from_branch"):
            db_filters["from_company"] = filters.get("from_branch")
        if filters.get("to_company"):
            db_filters["to_company"] = filters.get("to_company")

    elif transfer_type == "من شركة الي فرع":
        db_filters["from_type"] = "Customer"
        db_filters["to_type"] = "Branch"

        if filters.get("from_company"):
            db_filters["from_company"] = filters.get("from_company")
        if filters.get("to_branch"):
            db_filters["to_company"] = filters.get("to_branch")

    # common filters
    if from_date and to_date:
        db_filters["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        db_filters["posting_date"] = [">=", from_date]
    elif to_date:
        db_filters["posting_date"] = ["<=", to_date]

    if status:
        db_filters["status"] = status

    # fetch docs
    doc_list = frappe.get_all(
		"Internal Transfer",
		filters=db_filters,
		fields=[
			"name",
			"from_company",
			"to_company",
			"from_type",
			"to_type",
			"status",
			"posting_date",
			"amount",
			"phone_number",
		],
	)
    total_amount = 0
    for doc in doc_list:
        total_amount += doc.amount or 0
        data.append(
			{
				"ID": doc.name,
				"status": doc.status,
				"phone": doc.phone_number,
				"from_company": doc.from_company,
				"to_company": doc.to_company,
				"amount": doc.amount,
			}
		)

    # grouping field for chart
    group_by_field = "from_company" if reciver_or_sender == "Sender" else "to_company"

    # conditional WHERE clause dynamically
    conditions, values = [], []
    for k, v in db_filters.items():
        if isinstance(v, list):  # between or >= <=
            if v[0] == "between":
                conditions.append(f"{k} BETWEEN %s AND %s")
                values.extend(v[1])
            else:
                conditions.append(f"{k} {v[0]} %s")
                values.append(v[1])
        else:
            conditions.append(f"{k}=%s")
            values.append(v)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    totals = frappe.db.sql(
		f"""
		SELECT {group_by_field} as branch, COUNT(*) as total
		FROM `tabInternal Transfer`
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
					"name": status or "Count",
					"values": values_list,
				}
			],
		},
		"type": "bar",
		"colors": [
			"light-blue",
			"purple",
			"#ffa3ef",
		],
	}
    summary = [
		{"label": _("Total Transfers"), "value": len(doc_list), "indicator": "Blue"},
		{
			"label": _("Total Amount"),
			"value": total_amount,
			"datatype": "Currency",
			"indicator": "Green",
		},
		{
			"label": _("Pending Transfers"),
			"value": sum(1 for d in doc_list if d.status == "غير مستلمة"),
			"indicator": "Red",
		},
	]
    return data, chart, summary


def get_columns():
	return [
		{
			"fieldname": "ID",
			"label": _("ID"),
			"fieldtype": "Link",
			"options": "Internal Transfer",
		},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data"},
		{"fieldname": "phone", "label": _("Phone Number"), "fieldtype": "Data"},
		{"fieldname": "from_company", "label": _("From"), "fieldtype": "Data"},
		{"fieldname": "to_company", "label": _("To"), "fieldtype": "Data"},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency"},
	]
