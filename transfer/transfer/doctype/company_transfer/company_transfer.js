// Copyright (c) 2024, a and contributors
// For license information, please see license.txt
let type = 1;
let per_branch = null;
//transfer.transfer.doctype.company_transfer.company_transfer.get_profit_account




// Function to retrieve branch value with a callback
function fetchBranch(callback) {
    frappe.call({
        method: "transfer.transfer.doctype.company_transfer.company_transfer.get_branch",
        args: {
            // Pass any required parameters
        },
        callback: function (response) {
            if (response.message) {
                console.log("Branch value retrieved:", response.message);
                callback(null, response.message); // Pass value to callback
            } else {
                const errorMsg = __('حدث الخطاء الرجاء مراجعة الادمن كود الخطا 85247');
                console.error(errorMsg);
                callback(errorMsg, null); // Pass error to callback
            }
        },
        error: function (err) {
            console.error("Server error:", err);
            callback(err, null); // Handle server errors
        }
    });
}

 




frappe.ui.form.on('company transfer', {

    validate: function (frm) {

        if(frm.doc.from_company === frm.doc.to_company)
        {
            frappe.throw("لا يمكن التحويل الي نفس الشركة");
            validate = false;
        }

        if (type === 1) { //من شركة الي شركة
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Customer",
                    filters: { name: frm.doc.from_company },
                    fields: ["name"]
                },
                callback: function (response) {
                    if (!response.message || response.message.length === 0) {
                        frappe.msgprint(__('The company "{0}" is not linked to any customer.', [frm.doc.from_company]));
                        frappe.validated = false;
                    }
                }
            });
        }
        else {
            if (type === 2) {
                if (frm.doc.branch !== frm.doc.from_company)
                    frappe.throw(('الرجاء التاكد من الفرع'));
            }
        }
        if ((frm.doc.our_profit + frm.doc.other_party_profit) > frm.doc.amount) {
            frappe.throw(('الرجاء التحقق من القيمه والعمولات'));
        }

        validate = true
    },
    onload: function (frm) {

        frappe.realtime.on('doc_update', function(data) {
            if (cur_frm && cur_frm.docname === data.docname) {
                cur_frm.reload_doc();  // Reload the document to reflect changes
            }
        });
        fetchBranch(function (err, branchValue) {
            if (err) {
                frappe.msgprint(err); // Display error to the user
            } else {
                console.log("Branch value in onload:", branchValue);
                frm.set_value('branch', branchValue); // Use the retrieved value
                frm.trigger('branch');
            }
        });

        frappe.call({
            method: "transfer.transfer.doctype.company_transfer.company_transfer.get_branch",
            args: {
                  // Pass any parameters needed
            },
            callback: function(response) {
                if (response.message) {
                    per_branch = response.message; // Store value globally
                    console.log("Value retrieved and stored:", per_branch);
                } else {
                    frappe.throw(__('حدث الخطاء الرجاء مراجعة الادمن كود الخطا 85247'));
                }
            }
        });

        if (frm.doc.__islocal) {
           
            //default setting is من شركة الي شركة(شركات) Debtors - A
            frm.set_value("status", "غير مسجلة");
            frm.set_value("debit", "Debtors - A");
            frm.set_value("credit", "Debtors - A");
            frm.set_value("to_type", "Customer");
            frm.set_value("from_type", "Customer");
            frm.set_value("branch", per_branch);
            frm.refresh_fields();
            type = 1;
            frappe.show_alert("الرجاء اخال المعلومات ومراجعتها ثم الحفظ");
        }
        if (frm.doc.amended_from) {
            frappe.show_alert("تم تعديل الحوالة");
            frm.set_value("profit_account", ""); // Replace with your fieldname
            frm.set_value("journal_entry", ""); // Replace with your fieldname

        }
    },
    after_submit: function(frm){
            frm.reload_doc();
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
    profit_account: function(frm){
       

    },
    profit: function (frm) {
        frm.set_value('our_profit', frm.doc.profit);
        frm.set_value('other_party_profit', 0);
        if(frm.doc.profit )
        {
            if(!frm.doc.execution_amount)
            frm.set_value("execution_amount",frm.doc.amount + frm.doc.profit)
        }
    },
    select_external: function (frm) {

        if (frm.doc.select_external === "شركات") {
            frm.fields_dict['branch'].set_value(per_branch);
            frm.set_df_property("branch", "read_only", 1);
            frm.fields_dict['from_company'].set_value('');
            frm.set_value("debit","Debtors - A")

        }
        else {
            frm.set_df_property("branch", "read_only", 0);
            if (frm.doc.branch) {
                frm.set_df_property("from_company", "read_only", 0);
                frm.set_value("from_company", frm.doc.branch)
            }
        }
        if (frm.doc.select_external) {
            if (frm.doc.select_external === "شركات") {
                type = 1;
                frm.set_df_property("from_company", "hide", 0);
                frm.set_df_property("from_company", "read_only", 0);
                frm.set_value("to_type", "Customer");
                frm.set_value("from_type", "Customer");
            }

            if (frm.doc.select_external === "خارجي") {
                type = 2;
                frm.set_value('from_type',"Branch");
                frm.set_value('to_type',"Customer");
                frm.trigger('branch')
                frm.set_df_property("from_company", "read_only", 1);
            }
        }


    },
    from_company: function (frm) {

        //  frm.set_value('debit',"Debtors - A" );
        if(frm.doc.from_company)
        {
          //  frm.set_value("debit",frm.doc.profit_account) 
        }

    },
    debit: function(frm){
        // frappe.msgprint(frm.doc.debit)
    },
    to_company: function (frm) {

    },
    to_type: function (frm) {

    },
    from_type: function (frm) {
    },
    whatsapp_desc: function (frm) {
        if (frm.doc.whatsapp_desc) {
            let phoneNumber = extract_phone_number(frm.doc.whatsapp_desc);
            frm.set_value("phone_number", phoneNumber); // Set the phone number field
            frappe.show_alert({
                message: phoneNumber === "ادخل يدويا" ? "لا يمكن استخراج الرقم. ادخله يدوياً" : `تم استخراج الرقم: ${phoneNumber}`,
                indicator: phoneNumber === "ادخل يدويا" ? "red" : "green"
            });
        }
    },
    branch: function (frm) {

        //old code

        if (frm.doc.branch) {
            if (frm.doc.from_type == "Branch") {
                
                frappe.call({
                    method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_main_account', // Specify your server-side method here
                    args: {
                        branch: frm.doc.branch,
    
                    },
                    callback: function (r) {
                        if (r.message) {
                            // check if the account is found
                            frm.set_value('debit', r.message);
                        }
                    },
                    error: function (error) {
                        frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                        frm.set_value("debit", null)
                    }
                });


                frm.set_value("from_company", frm.doc.branch);
                frm.set_df_property("from_company", "read_only", 1);


            }


            frappe.call({
                method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_profit_account', // Specify your server-side method here
                args: {
                    branch: frm.doc.branch,

                },
                callback: function (r) {
                    if (r.message) {
                        // check if the account is found
                        frm.set_value('profit_account', r.message);
                    }
                },
                error: function (error) {
                    frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                    frm.set_value("branch", null)
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

    if (our_profit === other_party_profit) {
        frm.set_value('profit_is_splited', 1);
    }
    else {
        frm.set_value('profit_is_splited', 0);
    }

    // Refresh fields to reflect changes
    frm.refresh_fields();
}


//buttons 


// لم يضغط علي تم التسليم في الدوكيومتت غير مستلمة
frappe.ui.form.on('company transfer', {
    refresh: function (frm) {
        // const button = frm.fields_dict['go_to']?.$wrapper.find('button');
        if (frm.doc.docstatus == 1 && frm.doc.status === "غير مستلمة") {
            frm.add_custom_button(__('تم التسليم'), function () {
                frappe.confirm(
                    'هل انت متاكد من ان الحوالة من ان الحوالة سلمت  ؟',
                    function () {
                        // Confirmed action
                        frappe.call({
                            method: "transfer.transfer.doctype.company_transfer.company_transfer.handle_recived_transfer",
                            args: {
                                docname: frm.doc.name,
                                method: "submit"
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    // frappe.msgprint("Update successful!");
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function () {
                        // Cancelled action
                        frappe.msgprint(__('Action cancelled.'));
                    }
                );
            });
        }
        if (frm.doc.docstatus == 0 && frm.doc.status == "غير مسجلة" && !frm.is_new()) {
            frm.add_custom_button(__('تسجيل'), function () {
                frappe.confirm(
                    'هل انت متاكد من التسجيل  ؟',
                    function () {
                        // Confirmed action
                        frappe.call({
                            method: "transfer.transfer.doctype.company_transfer.company_transfer.handle_creation",
                            args: {
                                docname: frm.doc.name,
                                method: "submit"
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    // frappe.msgprint("Update successful!");
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function () {
                        // Cancelled action
                        frappe.msgprint(__('Action cancelled.'));
                    }
                );
            });
        }
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__('إلغاء الحوالة'), function () {
                frappe.confirm(
                    'هل انت متاكد من ان الحوالة سلمت ؟',
                    function () {

                        // Confirmed action
                        frappe.call({
                            method: "transfer.transfer.doctype.company_transfer.company_transfer.handle_cancel_transfer",
                            args: {
                                docname: frm.doc.name,
                                method: "cancel"
                            },
                            callback: function (r) {
                                if (!r.exc) {

                                    // frappe.msgprint("Update successful!");
                                    frm.reload_doc();
                                }
                            }
                        });


                    },
                    function () {
                        // Cancelled action
                        frappe.msgprint(__('الحوالة مسلمة مسبقا'));
                    }
                );
            });
        }
        else {
            
        }
    }
});

// إلغاء الحوالة سواء كانت مسلمة او غير مسلمة
// يتم إلغاءها وإلغاء القيود اذا تم الإلغاء في نفس اليوم
// غير ذالك يتم ارجاعها
 



// utils

function reset_fields(frm) {
    frm.set_value('from_company', '');
    frm.set_value('to_company', '');
}
//extract phone number from text(whatsapp_desc) 
// should start with 09 and it follows with 8 digits
function extract_phone_number(whatsapp_desc) {
    try {
        // Clean the text to remove spaces and hyphens
        let cleanedText = whatsapp_desc.replace(/[\s-]/g, "");

        // Match a phone number pattern with or without the country code
        let match = cleanedText.match(/(?:\+?218)?0?(9[1234]\d{7})/);

        if (match) {
            console.log("Matched phone number:", match[1]);
            return '0' + match[1]; // Return the matched phone number
        } else {
            console.log("No valid phone number found.");
            return "ادخل يدويا"; // Fallback if no match
        }
    } catch (error) {
        console.error("Error in extract_phone_number:", error);
        return "ادخل يدويا"; // Fallback for unexpected errors
    }
}
