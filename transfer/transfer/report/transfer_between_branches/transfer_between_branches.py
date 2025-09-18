# Copyright (c) 2025, awad mohamed & atta almanan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns( )
	data,chart = get_data_chart(filters=filters)
	return columns, data , None , chart


def get_data_chart(filters=None):
	data = []
	from_date = filters.pop("from_date", None)
	to_date = filters.pop("to_date", None)
	from_branch = filters.pop('branch',None)
	
	# build db filters from  filters
	db_filters = filters.copy()

	if from_branch :
		db_filters["from_branch"] = ["=",from_branch]
	if from_date and to_date:
		db_filters["posting_date"] = ["between", [from_date, to_date]]
	elif from_date:
		db_filters["posting_date"] = [">=", from_date]
	elif to_date:
		db_filters["posting_date"] = ["<=", to_date]

	doc_list = frappe.get_all(
		"transfer between branches",
		filters=db_filters,
		fields=["name", "from_branch", "to_branch", "workflow_state", "posting_date","amount","phone_number"]
	)
	print(doc_list)
	for doc in doc_list:
		d = {"ID": doc["name"]}
		docs = frappe.get_doc("transfer between branches", doc['name'])
		d["status"] =  docs.workflow_state
		d["phone"] =  docs.phone_number
		d["from_branch"] =  docs.from_branch
		d["to_branch"] =  docs.to_branch
		d["amount"] =  docs.amount
		data.append(d)
		
	totals = frappe.db.sql("""
		SELECT from_branch, COUNT(*) as total
		FROM `tabtransfer between branches`
		WHERE workflow_state=%s
		GROUP BY from_branch
	""", (filters.workflow_state,), as_dict=True)

	#  labels and values
	branches_list = [row["from_branch"] for row in totals]
	values = [row["total"] for row in totals]

	chart = {
		"data": {
			"labels": branches_list,
			"datasets": [
				{
					"name": filters.workflow_state,
					"values": values
				}
			]
		},
		"type": "bar"
	}
	return data,chart


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
			"label": _("Recived Branch"),
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
