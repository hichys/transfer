 
frappe.query_reports["company transfer"] = {
	"filters": [
		{
			fieldname: "from_company",
			label: __("Sender Company"),
			fieldtype: "Link",
			options: "Customer",
			get_query: function () {
				const to_company = frappe.query_report.get_filter_value('to_company');
				let filters = { "customer_type": "Company" };

				if (to_company) {
					filters["name"] = ["!=", to_company];
				}

				return { filters: filters };
			}
		},
		{
			fieldname: "to_company",
			label: __("Receiver Company"),
			fieldtype: "Link",
			options: "Customer",
			get_query: function () {
				const from_company = frappe.query_report.get_filter_value('from_company');
				let filters = { "customer_type": "Company" };

				if (from_company) {
					filters["name"] = ["!=", from_company];
				}

				return { filters: filters };
			}
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				'مستلمة',
				'غير مستلمة',
				'ملغية',
				'غير مسجلة'
			],
			default: 'غير مستلمة',
			reqd: 1
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
			label: __("filter by Reciver or Sender"),
			fieldtype: "Select",
			options: ['Reciver', 'Sender'],
			default: "Sender",
			reqd: 1
		},


	]
};
