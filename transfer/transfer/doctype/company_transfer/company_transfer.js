// Copyright (c) 2024, a and contributors
// For license information, please see license.txt

frappe.ui.form.on('company transfer', {
    validate: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.set_value('status', 'غير مستلمة'); // Replace 'Draft' with custom status
            frappe.show_alert(frm.doc.status)
        }
        if (frm.doc.docstatus === 2) {
            frm.set_value('status', 'ملغية'); // Replace 'Cancelled' with custom status
            frappe.show_alert(frm.doc.status)
        }
    },
    profit_is_splited: function (frm) {
        //make our_profit and other_party_profit same
        if (frm.doc.profit_is_splited) {

            const profit = frm.doc.profit || 0;
            const our_profit = frm.doc.profit / 2 || 0; 

            frm.set_value('our_profit', our_profit);
            frm.set_value('other_party_profit', our_profit);
        }
    },
    amount: function (frm) {
        calculate_profit_or_loss(frm);
    },
    execution_amount: function (frm) {
        calculate_profit_or_loss(frm);
    },
    other_party_profit: function (frm) {
        adjust_profits(frm, 'other_party_profit');
    },
    our_profit: function (frm) {
        adjust_profits(frm, 'our_profit');
    },
    profit: function (frm) {
        frm.set_value('our_profit', frm.doc.profit);
        frm.set_value('other_party_profit', 0);
    },
    checkbox_external_transfer: function (frm) {
        if (frm.doc.checkbox_external_transfer) {
            frappe.show_alert("تحويلة خارجية");

            frm.set_value('branch', 'الفرناج').then(() => {
                frm.set_df_property('branch', 'read_only', 1);
            });
        } else {
            frappe.show_alert("تحويلة داخلية");
            frm.set_df_property('branch', 'read_only', 0);
        }
    },
    from_company: function (frm) {
       if(frm.doc.checkbox_external_transfer)
       {
        frm.set_value('debit',"Debtors - A" );
       }
    },
    to_company: function (frm) {
        // Refresh logic if needed
        frm.set_value('credit',"Debtors - A" );
    },
    branch:function(frm){
        if(frm.doc.branch){
            frm.set_value('profit_account','0099 - عمولات الفرناج - A' );
        }
    },
    refresh: function (frm) {
        // Refresh logic if needed
    }
});

// Utility Functions

function calculate_profit_or_loss(frm) {
    const amount = frm.doc.amount || 0;
    const execution_amount = frm.doc.execution_amount || 0;

    if (amount > 0 && execution_amount > 0) {
        const profit = amount - execution_amount;

        // Update profit field
        frm.set_value('profit', profit);

        // Set default profit allocation
        frm.set_value('our_profit', profit);
        frm.set_value('other_party_profit', 0);

        // Determine without profit status
        frm.set_value('without_profit', profit === 0 ? 1 : 0);
        frappe.show_alert(profit === 0 ? "بدون عمولة" : "بعمولة");

        // Show profit/loss status
        if (profit < 0) {
            frappe.show_alert("الحوالة منفذه بالخسارة");
        } else if (profit > 0) {
            frappe.show_alert("الحوالة منفذه بالربح");
        } else {
            frappe.show_alert("الحوالة بدون ربح أو خسارة");
        }
    } else {
        // Reset profit fields if values are missing
        frm.set_value('profit', 0);
        frm.set_value('other_party_profit', 0);
        frm.set_value('our_profit', 0);
    }

    frm.refresh_fields();
}

function adjust_profits(frm, changed_field) {
    const profit = frm.doc.profit || 0;
    let our_profit = frm.doc.our_profit || 0;
    let other_party_profit = frm.doc.other_party_profit || 0;

    // Adjust the other field to ensure the total equals profit
    if (changed_field === 'our_profit') {
        other_party_profit = profit - our_profit;

        // Prevent invalid adjustments
        if (other_party_profit < 0 && profit >= 0) {
            frappe.msgprint("The other party's profit cannot be negative when total profit is positive.");
            other_party_profit = 0;
            our_profit = profit;
        } else if (other_party_profit > 0 && profit < 0) {
            frappe.msgprint("The other party's profit cannot be positive when total profit is negative.");
            other_party_profit = 0;
            our_profit = profit;
        }
    } else if (changed_field === 'other_party_profit') {
        our_profit = profit - other_party_profit;

        // Prevent invalid adjustments
        if (our_profit < 0 && profit >= 0) {
            frappe.msgprint("Our profit cannot be negative when total profit is positive.");
            our_profit = 0;
            other_party_profit = profit;
        } else if (our_profit > 0 && profit < 0) {
            frappe.msgprint("Our profit cannot be positive when total profit is negative.");
            our_profit = 0;
            other_party_profit = profit;
        }
    }

    // Update the fields
    frm.set_value('our_profit', our_profit);
    frm.set_value('other_party_profit', other_party_profit);

    if(our_profit === other_party_profit){
        frm.set_value('profit_is_splited', 1);
    }
    else{
        frm.set_value('profit_is_splited', 0);
    }

    // Refresh fields to reflect changes
    frm.refresh_fields();
}
