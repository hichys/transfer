// Copyright (c) 2025, awad mohamed & atta almanan and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Simple Sales", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Simple Sales', {
    onload: function (frm) {
        // Default payment mode to "Cash"
        frm.set_value('payment_mode', 'Cash');
    },
    quantity: function (frm) {
        // Auto-calculate amount
        frappe.call({
            method: "transfer.transfer.doctype.simple_sales.simple_sales.get_currency_selling_rate",
            args: {
                base_currency: "LYD",
                target_currency: "SDG"
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('rate', r.message);
                    frm.set_value('amount', frm.doc.quantity * frm.doc.rate);
                } else {
                    console.log("No rate found.");
                    frappe.throw("Please set currency exchange rate");
                }
            }
        });




    },
    rate: function (frm) {
        // Auto-calculate amount
        frm.set_value('amount', frm.doc.quantity * frm.doc.rate);
    },
    discount: function (frm) {
        frm.set_value('grand_total', frm.doc.amount - frm.doc.discount)
    },
    to: function (frm) {

    }
});
frappe.ui.form.on('Simple Sales', {
    refresh: function (frm) {
        // Call the backend to fetch linked Payment Entries and Sales Invoices
        frappe.call({
            method: 'transfer.transfer.doctype.simple_sales.simple_sales.get_related_documents',
            args: {
                simple_sales_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    // Update Payment Entries table
                    const payment_entries = r.message.payment_entries || [];


                    // Update Sales Invoices table
                    payment_entries.forEach(pe => {
                        frm.add_custom_button(
                            `${__('Payment Entry')} - ${pe.name}`,
                            function () {
                                frappe.set_route('Form', 'Payment Entry', pe.name);
                            },
                            __('View')
                        );
                    });

                }
            }
        });
    }
});
