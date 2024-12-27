// Copyright (c) 2024, a and contributors
// For license information, please see license.txt

frappe.ui.form.on("transfer between branches", {
	refresh(frm) {
        let selected_status = frm.doc.status;  // Replace 'status' with your select fieldname
        console.log("Selected status:", selected_status);
	},
});
