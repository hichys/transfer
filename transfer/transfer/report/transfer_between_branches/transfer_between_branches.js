// Copyright (c) 2025, awad mohamed & atta almanan and contributors
// For license information, please see license.txt

frappe.query_reports["Transfer Between Branches"] = {
	"filters": [
		{
			fieldname : "branch",
			label : __("Branch"),
			fieldtype: "Link",
			options : ('Branch')
		},
		{
			fieldname : "workflow_state",
			label : __("Status"),
			fieldtype: "Select",
			options: [
					'مستلمة',
					'غير مستلمة',
					'ملغية',
					'غير مسجلة'
					],
			default: 'غير مستلمة',
			reqd : 1
		},
		{
			fieldname : "from_date",
			label : __("From Date"),
			fieldtype: "Date",
			default : frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd : 1
		},
		{
			fieldname : "to_date",
			label : __("To Date"),
			fieldtype: "Date",
			default : frappe.datetime.get_today(),
			reqd : 1
		},

	]
};
