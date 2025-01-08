// Copyright (c) 2025, a and contributors
// For license information, please see license.txt

//


let type = 2;
frappe.ui.form.on("Internal Transfer", {

   
    /**
     * التاكد من ان حقل المرسل والستقبل يحتوي علي قيم صحيحه
     * 
     */
    validate: function(frm) {
        if (type === 1) { //من شركة الي فرع
            
            if(frm.doc.branch !== frm.doc.to_company)
                frappe.throw(('الرجاء التاكد من الفرع'));
            
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Customer",
                    filters: { name: frm.doc.from_company },
                    fields: ["name"]
                },
                callback: function(response) {
                    if (!response.message || response.message.length === 0) {
                        frappe.msgprint(__('The company "{0}" is not linked to any customer.', [frm.doc.from_company]));
                        frappe.validated = false;
                    }
                }
            });
        }
        else{
            if(type === 2)
            {
                if(frm.doc.branch !== frm.doc.from_company)
                    frappe.throw(('الرجاء التاكد من الفرع'));
            }
        }
        if ((frm.doc.our_profit + frm.doc.other_party_profit )> frm.doc.amount) {
            frappe.throw(('الرجاء التحقق من القيمه والعمولات'));
        }

        validate = true
    },

    refresh : function(frm){
        if (frm.doc.docstatus === 1   && frm.doc.status === "غير مسجلة") {
            frm.add_custom_button(__('تسجيل'), function () {
                frappe.confirm(
                    'Are you sure you want to proceed?',
                    () => {
                        // Action to take if user confirms
                        frappe.call({
                            method: 'transfer.transfer.doctype.internal_transfer.internal_transfer.handel_journal_entries_creation',
                            args: {
                                docname: frm.doc.name
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('Action completed successfully.'));
                                    frm.reload_doc(); // Reload document to reflect changes
                                }
                            }
                        });
                    },
                    () => {
                        frappe.msgprint(__('Action was canceled.'));
                    }
                );
            });
        }

        if (frm.doc.docstatus === 1 && frm.doc.status === "غير مستلمة") {
            frm.add_custom_button(__('تم التسليم'), function () {
                frappe.confirm(
                    'هل انت متاكد من ان الحوالة سلمت ؟',
                    () => {
                        // Action to take if user confirms
                        frappe.call({
                            method: 'transfer.transfer.doctype.internal_transfer.internal_transfer.transfer_completed',
                            args: {
                                docname: frm.doc.name
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('تم تغير حالة الحوالة بنجاح'));
                                    frm.reload_doc(); // Reload document to reflect changes
                                }
                            }
                        });
                    },
                    () => {
                        frappe.msgprint(__('Action was canceled.'));
                    }
                );
            });
        }

        if (frm.doc.docstatus === 1 && frm.doc.status === "مستلمة") {
            frm.add_custom_button(__('إلغاء'), function () {
                frappe.confirm(
                    'هل انت متاكد من الإلغاء ؟',
                    () => {
                        // Action to take if user confirms
                        frappe.call({
                            method: 'transfer.transfer.doctype.internal_transfer.internal_transfer.handel_cancellation',
                            args: {
                                docname: frm.doc.name
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('Action completed successfully.'));
                                    frm.reload_doc(); // Reload document to reflect changes
                                }
                            }
                        });
                    },
                    () => {
                        frappe.msgprint(__('Action was canceled.'));
                    }
                );
            });
        }
    },
    without_profit : function(frm){
        if(frm.doc.without_profit){
            frappe.show_alert(frm.doc.our_profit);
            frappe.show_alert(frm.doc.other_party_profit);
        }
    },
    amount: function (frm) {
    },
    execution_amount: function (frm) {
    },
    other_party_profit: function (frm) {
    },
    our_profit: function (frm) {
    },
    profit: function (frm) {
        frm.set_value('our_profit', frm.doc.profit);
        frm.set_value('other_party_profit', 0);
    },
    select_internal:function (frm){

        
        

        if(frm.doc.select_internal == "من شركة الي فرع"){
            frappe.show_alert("من شركة الي فرع 2525");
           
            // frm.fields_dict['from_type'].set_value("Customer");
            // frm.fields_dict['to_type'].set_value("Branch");
            frm.set_value('from_type','Customer');
            frm.set_value('to_type','Branch');
            frm.set_df_property('from_company', 'label', 'من شركة ');
            frm.set_df_property('to_company', 'label', 'الي فرع ال');
            type = 1;
            frm.set_df_property('to_comapny','read_only',1)
            frm.set_df_property('from_company','read_only',0)


        }
        if(frm.doc.select_internal == "من فرع الي شركة"){
            frappe.show_alert("من شركة الي فرع 2525");
             
            frm.set_value('from_type','Branch');
            frm.set_value('to_type','Customer');
            frm.set_df_property('from_company', 'label', 'من فرع ال');
            frm.set_df_property('to_company', 'label', 'الي شركة ');
             type = 2;

             frm.set_df_property('from_company','read_only',1)
             frm.set_df_property('to_comapny','read_only',0)
        }

        //clear field for new inputs
      
        if(frm.select_internal)
            {
                frm.fields_dict['from_company'].set_value("")
                frm.fields_dict['branch'].set_value("")
                frm.fields_dict['to_company'].set_value("")
                
                frm.refresh_fields()
             
            }
    },
    without_profit: function(frm){

        frm.set_value('our_profit',0)
        frm.set_value('other_party_profit',0)
    },
    branch: function (frm){
        if(frm.doc.branch){
            if(type === 1){
                frappe.show_alert("من شركة الي فرع")
                frm.set_value('to_company',frm.doc.branch)
                frm.set_df_property('to_comapny','read_only',1)
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
                    frm.set_df_property('from_company','read_only',1)

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


