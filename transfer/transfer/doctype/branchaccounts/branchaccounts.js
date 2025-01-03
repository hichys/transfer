// Copyright (c) 2024, a and contributors
// For license information, please see license.txt

// frappe.ui.form.on("BranchAccounts", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('BranchAccounts', {
    refresh: function(frm) {
        // Add button to form
        frm.add_custom_button(__('Generate'), function() {
            // When button is clicked, trigger the function
            frappe.call({
                method: "transfer.transfer.doctype.branchaccounts.branchaccounts.generate_accounts",
                args: {},
                callback: function(response) {
                    // Handle the response here
                    if(response.message) {
                        frappe.msgprint(response.message);
                    }
                },
                error: function(err) {
                    // Handle error
                    frappe.msgprint(__('Error occurred while processing: ') + err);
                }
            });
        });
    }
});
