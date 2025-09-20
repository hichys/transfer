// Copyright (c) 2025
// For license information, please see license.txt

frappe.query_reports["internal transfer"] = {
	onload: function (report) {
		// Apply filter display logic when the report loads
		const type = frappe.query_report.get_filter_value('type');
		toggle_filters(type);
	},

	"filters": [
		{
			fieldname: "type",
			label: __("Type"),
			fieldtype: "Select",
			options: [
				'',
				'من فرع الي شركة',
				'من شركة الي فرع',
			],
			default: 'من فرع الي شركة',
			on_change: function () {
				const type = frappe.query_report.get_filter_value('type');
				toggle_filters(type);
				frappe.query_report.refresh();
			}
		},
		{ fieldname: "from_branch", label: __("From Branch"), fieldtype: "Link", options: "Branch" },
		{ fieldname: "to_company", label: __("To Company"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "from_company", label: __("From Company"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "to_branch", label: __("To Branch"), fieldtype: "Link", options: "Branch" },
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ['','مستلمة', 'غير مستلمة', 'ملغية', 'غير مسجلة'],
			default: '',
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "reciver_or_sender",
			label: __("Filter by Receiver or Sender"),
			fieldtype: "Select",
			options: ['Reciver', 'Sender'],
			default: "Sender",
			reqd: 1
		},
	]
};

// Helper function to toggle filters
function toggle_filters(type) {
	if (type === 'من فرع الي شركة') {
		frappe.query_report.toggle_filter_display('from_branch', false);
		frappe.query_report.toggle_filter_display('to_company', false);

		frappe.query_report.toggle_filter_display('from_company', true);
		frappe.query_report.toggle_filter_display('to_branch', true);
	} else {
		frappe.query_report.toggle_filter_display('from_company', false);
		frappe.query_report.toggle_filter_display('to_branch', false);

		frappe.query_report.toggle_filter_display('from_branch', true);
		frappe.query_report.toggle_filter_display('to_company', true);
	}
}
