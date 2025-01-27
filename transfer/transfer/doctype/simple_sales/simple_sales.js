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
        if (frm.doc.docstatus === 1) {

            // Call the backend to fetch linked Payment Entries and Sales Invoices
            frappe.call({
                method: 'transfer.transfer.doctype.simple_sales.simple_sales.get_related_documents',
                args: {
                    simple_sales_name: frm.doc.name
                },
                callback: function (r) {
                    if (frm.doc.si) {
                        frm.add_custom_button(
                            `${__('Sales Invoice')} - ${frm.doc.si}`,
                            function () {
                                frappe.set_route('Form', 'Sales Invoice', frm.doc.si);
                            },
                            __('View')
                        );
                    }
                    else
                        if (r.message) {
                            const payment_entries = r.message.payment_entries || [];
                            const sales_invoice = r.message.sales_invoice;

                            // Add custom buttons for Payment Entries
                            payment_entries.forEach(pe => {
                                frm.add_custom_button(
                                    `${__('Payment Entry')} - ${pe.name}`,
                                    function () {
                                        frappe.set_route('Form', 'Payment Entry', pe.name);
                                    },
                                    __('View')
                                );
                            });

                            // Update Sales Invoice field and add a button if found


                            if (sales_invoice) {
                                frm.add_custom_button(
                                    `${__('Sales Invoice')} - ${sales_invoice}`,
                                    function () {
                                        frappe.set_route('Form', 'Sales Invoice', sales_invoice);
                                    },
                                    __('View')
                                );
                            } else {

                            }
                        }
                }
            });
        }

    }
});
