// Copyright (c) 2025, a and contributors
// For license information, please see license.txt

//


let type = 2;
frappe.ui.form.on("Internal Transfer", {

    onload(frm){
        frm.set_value('select_internal',"من فرع الي شركة")
        frm.set_value('from_type','Branch')
        frm.set_value('to_type','Customer')
        frm.refresh_fields()
    } ,
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
	refresh(frm) {

	},
    select_internal:function (frm){
        if(frm.doc.select_internal == "من شركة الي فرع"){
            frappe.show_alert("من شركة الي فرع 2525");
           
            // frm.fields_dict['from_type'].set_value("Customer");
            // frm.fields_dict['to_type'].set_value("Branch");
            frm.set_value('from_type','Customer')
            frm.set_value('to_type','Branch')
            frm.set_df_property('from_company', 'label', 'من شركة ');
            frm.refresh_field('from_company');
            frm.set_df_property('to_company', 'label', 'الي فرع ال');
            frm.refresh_field('to_company');
            type = 1;

        }
        if(frm.doc.select_internal == "من فرع الي شركة"){
            frappe.show_alert("من شركة الي فرع 2525");
             
            frm.set_df_property('from_company', 'label', 'من فرع ال');
            frm.refresh_field('from_company');
            frm.set_df_property('to_company', 'label', 'الي شركة ');
            frm.refresh_field('to_company');
            frm.set_value('from_type','Branch')
            frm.set_value('to_type','Customer')
             type = 2;
        }
         
    },
    branch: function (frm){
        if(frm.doc.branch){
            if(type === 1){
                frappe.show_alert("من شركة الي فرع")
                frm.set_value('to_company',frm.doc.branch)

                frappe.call({
                    method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_temp_account', // Specify your server-side method here
                    args: {
                        branch: frm.doc.branch,
                        
                    },
                    callback: function(r) {
                        if (r.message) {
                            // check if the account is found
                            frm.set_value('profit_account', r.message);
                            frm.set_value('credit',r.message)
                            frm.set_value('debit',"Debtors - A")
                        }
                    },
                    error: function(error) {
                        frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                    }
                });
            }
            else{
                
                if(type === 2)
                {
                    frappe.show_alert("من فرع الي شركة")
                    frm.set_value('from_company',frm.doc.branch)

                    frappe.call({
                        method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_main_account', // Specify your server-side method here
                        args: {
                            branch: frm.doc.branch,
                            
                        },
                        callback: function(r) {
                            if (r.message) {
                                // check if the account is found
                                frm.set_value('profit_account', r.message);
                                frm.set_value('debit',r.message)
                                frm.set_value('credit',"Debtors - A")
                                
                            }
                        },
                        error: function(error) {
                            frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                        }
                    });

                }
            }


           
        }
    },
    from_type: function(frm){
        reset_fields(frm);
    },
    


    





    
});
function reset_fields(frm){
    frm.set_value('from_company','');
    frm.set_value('to_company',''); 
    frm.set_value('branch','')
    frm.set_value('profit_account','')
    frm.set_value('credit','')
    frm.set_value('debit','')
    frm.refresh_fields()
}


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
