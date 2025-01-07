// Copyright (c) 2024, a and contributors
// For license information, please see license.txt

frappe.ui.form.on('company transfer', {
            onload: function(frm) {
                if (frm.doc.amended_from) {
                    frappe.show_alert("تم تعديل الحوالة");
                    frm.set_value("profit_account", ""); // Replace with your fieldname
                    frm.set_value("journal_entry", ""); // Replace with your fieldname
                    frm.set_value("status", "غير مستلمة");
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
        if (frm.doc.checkbox_external_transfer  ) {
            frappe.show_alert("تحويلة خارجية");
            frm.set_value("checkbox_internal_transfer", 0);
            frm.set_value('branch', 'العالمية الفرناج').then(() => {
            });
            
            frm.set_df_property("branch", "read_only", 0);
            frm.set_df_property("to_company", "read_only", 0);
            
            
            frm.fields_dict['from_type'].set_value("Customer");
            frm.fields_dict['to_type'].set_value("Customer");
        }  
        
    },
    select_external:function (frm){

       
            if(frm.doc.select_external == "من شركة الي شركة"){
                frm.fields_dict['from_type'].set_value("Customer");
                frm.fields_dict['to_type'].set_value("Customer");
            }
    
            if(frm.doc.select_external == "خارجي"){
                frm.set_value('from_company','');
                frm.set_value('branch','');
               
                frm.fields_dict['from_type'].set_value("Branch");
                frm.fields_dict['to_type'].set_value("Customer");
                
            }
     
     
    },
    select_internal:function (frm){
        if(frm.doc.select_internal == "من شركة الي فرع"){
            frappe.show_alert("من شركة الي فرع 2525");
             
            frm.fields_dict['from_type'].set_value("Customer");
            frm.fields_dict['to_type'].set_value("Branch");
             
        }
        if(frm.doc.select_internal == "من فرع الي شركة"){
            frappe.show_alert("من شركة الي فرع 2525");
             
            frm.fields_dict['from_type'].set_value("Branch");
            frm.fields_dict['to_type'].set_value("Customer");
             
        }
         
    },
    checkbox_internal_transfer: function (frm) {
        if (frm.doc.checkbox_internal_transfer) {
            frappe.show_alert("تحويلة داخلية");
            frm.set_value("checkbox_external_transfer", 0);
            frm.set_value('branch', 'العالمية الفرناج').then(() => {
                
            });
            frm.fields_dict['from_type'].set_value("Customer");
            frm.fields_dict['to_type'].set_value("Branch");
            // set branch title to : الي فرع 
            frm.set_df_property("branch", "label", "من فرع ؟");
        
            // Make the field read-only (disabled)
            frm.set_df_property("branch", "read_only", 1);
            frm.set_df_property("to_company", "read_only", 1);

            // Refresh the field to apply the changes
            frm.refresh_field("branch");
        } 
    },
    from_company: function (frm) {
       if(frm.doc.checkbox_external_transfer)
       {
            //  frm.set_value('debit',"Debtors - A" );
       }
    },
    to_company: function (frm) {
        // Refresh logic if needed
        frm.set_value('credit',"Debtors - A" );
    },
    to_type: function(frm) {
        frm.refresh_fields(); 
    },
    from_type: function(frm){
        frm.refresh_fields()
    },
    branch:function(frm){
        if(frm.doc.branch){
            frappe.call({
                method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_profit_account', // Specify your server-side method here
                args: {
                    branch: frm.doc.branch,
                    
                },
                callback: function(r) {
                    if (r.message) {
                        // check if the account is found
                        frm.set_value('profit_account', r.message);
                        
                    }
                },
                error: function(error) {
                    frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                }
            });
            
        }
    },
    
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


//buttons 


// لم يضغط علي تم التسليم في الدوكيومتت غير مستلمة
frappe.ui.form.on('company transfer', {
    refresh: function(frm) {
        const button = frm.fields_dict['go_to']?.$wrapper.find('button');

        if (button) {
            // Add custom HTML or attributes to the button
            button.html('<i class="fa fa-check"></i> Custom Button');
            button.css({
                'background-color': '#4CAF50', // Custom styling
                'color': 'white'
            });
        }
        if(frm.doc.docstatus == 0)
        {
            frm.add_custom_button(__('تم التسليم'), function() {
                frappe.confirm(
                    'هل انت متاكد من ان الحوالة من ان الحوالة سلمت  ؟',
                    function() {
                        // Confirmed action
                        frappe.call({
                            method: "transfer.transfer.doctype.company_transfer.company_transfer.handle_recived_transfer",
                            args: {
                                    docname: frm.doc.name,
                                    method : "submit"
                                 },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint("Update successful!");
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function() {
                        // Cancelled action
                        frappe.msgprint(__('Action cancelled.'));
                    }
                );
            });
        }
    }
});

// إلغاء الحوالة سواء كانت مسلمة او غير مسلمة
// يتم إلغاءها وإلغاء القيود اذا تم الإلغاء في نفس اليوم
// غير ذالك يتم ارجاعها
frappe.ui.form.on('company transfer', {
    refresh: function(frm) {
        if(frm.doc.docstatus ==1  )
        {
            frm.add_custom_button(__('إلغاء الحوالة'), function() {
                frappe.confirm(
                    'هل انت متاكد من ان الحوالة سلمت ؟',
                    function() {
                        
                        // Confirmed action
                        frappe.call({
                            method: "transfer.transfer.doctype.company_transfer.company_transfer.handle_cancel_transfer",
                            args: {
                                    docname: frm.doc.name,
                                    method : "cancel"
                                 },
                            callback: function(r) {
                                if (!r.exc) {
                                    
                                    frappe.msgprint("Update successful!");
                                    frm.reload_doc();
                                }
                            }
                        });

                       
                    },
                    function() {
                        // Cancelled action
                        frappe.msgprint(__('الحوالة مسلمة مسبقا'));
                    }
                );
            });
        }
        else{
             
        }
    }
});
