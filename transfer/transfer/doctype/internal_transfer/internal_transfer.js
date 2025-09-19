// Copyright (c) 2025, a and contributors
// For license information, please see license.txt

//
frappe.ui.form.on('Internal Transfer', {
    create_journal_entry: function (frm) {
        frappe.call({
            method: 'transfer.transfer.doctype.internal_transfer.internal_transfer.create_journal_entry_preview',
            args: { doctype: frm.doctype, docname: frm.doc.name },
            callback: function (r) {
                if (r.message) {
                    const details = r.message;

                    // Display a dialog with transaction details
                    const dialog = new frappe.ui.Dialog({
                        title: 'تأكيد العملية',
                        fields: [
                            {
                                fieldname: 'details_html',
                                fieldtype: 'HTML',
                                options: `
                                    <div style="direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; line-height: 1.8;">
                                        <h4 style="color: #333;">تفاصيل العملية:</h4>
                                        <p><strong>الفرع:</strong> ${details.branch}</p>
                                        <p><strong>المرسل:</strong> ${details.from_company}</p>
                                        <p><strong>المستقبل:</strong> ${details.to_company}</p>
                                        <p><strong>القيمة:</strong> ${details.amount}</p>
                                        <p><strong>عمولة <span style="color: #007bff;">${details.from_company}</span>:</strong> ${details.profit}</p>
                                        <p><strong>عمولة <span style="color: #007bff;">${details.to_company}</span>:</strong> ${details.other_party_profit}</p>
                                        <button id="copy-details" class="btn btn-secondary" style="margin-top: 15px;">نسخ التفاصيل</button>
                                    </div>
                                `,
                            },
                        ],
                        primary_action_label: 'تأكيد',
                        primary_action: function () {
                            frappe.call({
                                method: 'transfer.transfer.doctype.internal_transfer.internal_transfer.handel_journal_entries_creation',
                                args: { docname: frm.doc.name },
                                callback: function (r) {
                                    if (r.message.status === 'success') {
                                        frappe.msgprint('تم إنشاء القيد بنجاح.');
                                        dialog.hide();
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    });

                    // Show the dialog
                    dialog.show();

                    // Add "copy details" functionality
                    dialog.$wrapper.on('click', '#copy-details', function () {
                        const detailsText = `
                            الفرع: ${details.branch}
                            المرسل: ${details.from_company}
                            المستقبل: ${details.to_company}
                            القيمة: ${details.amount}
                            عمولة ${details.from_company}: ${details.profit}
                            عمولة ${details.to_company}: ${details.other_party_profit}
                        `;
                        navigator.clipboard.writeText(detailsText).then(() => {
                            frappe.show_alert('تم نسخ التفاصيل إلى الحافظة.');
                        }).catch(err => {
                            frappe.msgprint('حدث خطأ أثناء نسخ النص.');
                        });
                    });
                }
            }
        });
    }
});

let type = 2;
frappe.ui.form.on("Internal Transfer", {

    onload: function (frm) {
        if (frm.doc.__islocal) {
            frappe.show_alert("جديدة");
            // frm.set_value("select_internal","من فرع الي شركة");
            // frm.set_value("to_type","Customer");
            // frm.set_value("from_type","Branch");
            // frm.refresh_fields(); 
            frm.trigger("select_internal")
        }
    },

    delete_draft: function (frm) {
        frappe.confirm(
            'هل انت متاكد من المسح ؟',
            function () {
                frappe.call({
                    method: 'transfer.transfer.doctype.internal_transfer.internal_transfer.delete_draft_doc',
                    args: {
                        doctype: frm.doc.doctype,
                        docname: frm.doc.name
                    },
                    callback: function (response) {
                        frappe.msgprint(response.message);
                        frappe.set_route('List', frm.doc.doctype); // Redirect to the list view after deletion
                    }
                });
            }
        );
    },
    /**
     * التاكد من ان حقل المرسل والستقبل يحتوي علي قيم صحيحه
     * 
     */
    validate: function (frm) {

        if (type === 1) { //من شركة الي فرع

            if (frm.doc.branch !== frm.doc.to_company)
                frappe.throw(('الرجاء التاكد من الفرع'));

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
    after_save: function (frm) {
    },
    refresh: function (frm) {

        if (!frm.doc.__islocal) {
            if (frm.doc.docstatus === 0 || frm.doc.status === "غير مسجلة") {  // Show the delete button only for draft documents
                frm.add_custom_button('مسح الحوالة', function () {
                    frm.trigger('delete_draft');
                });
            }
        }

        if (frm.doc.docstatus === 1 && frm.doc.status === "غير مسجلة") {
            frm.add_custom_button(__('تسجيل'), function () {
                frm.trigger('create_journal_entry');
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

        if (frm.doc.docstatus === 1 && frm.doc.status === "مستلمة" || frm.doc.status === "غير مستلمة") {
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
    delivery_date: function (frm) {
        if (frm.doc.delivery_date && frm.doc.posting_date) {
            const deliveryDate = frappe.datetime.str_to_obj(frm.doc.delivery_date);
            const postingDate = frappe.datetime.str_to_obj(frm.doc.posting_date);

            if (deliveryDate < postingDate) {
                frappe.msgprint(__('تاريخ التسليم خطأ'));
                frm.set_value('delivery_date', null);
            }
        }
    },
    profit_is_splited: function (frm) {
        console.log(frm.doc.profit_is_splited);
        //make our_profit and other_party_profit same
        if (frm.doc.profit_is_splited) {

            const profit = frm.doc.profit || 0;
            const our_profit = frm.doc.profit / 2 || 0;

            frm.set_value('our_profit', our_profit);
            frm.set_value('other_party_profit', our_profit);
        }
    },
    amount: function (frm) {
    },
    execution_amount: function (frm) {
    },
    other_party_profit: function (frm) {
        adjust_profits(frm, 'other_party_profit');
    },
    our_profit: function (frm) {
        adjust_profits(frm, 'our_profit');
    },
    profit: function (frm) {
        frm.set_value('our_profit', frm.doc.profit/2);
        frm.set_value('other_party_profit', frm.doc.profit/2);
    },
    select_internal: function (frm) {

        if (frm.doc.select_internal) {
            reset_fields(frm);
        }


        if (frm.doc.select_internal == "من شركة الي فرع") {
            frappe.show_alert("من شركة الي فرع");
            // frm.fields_dict['from_type'].set_value("Customer");
            // frm.fields_dict['to_type'].set_value("Branch");
            frm.set_value('from_type', 'Customer');
            frm.set_value('to_type', 'Branch');

            frm.set_df_property('other_party_profit', 'read_only', 0);
            frm.set_df_property('from_company', 'label', 'من شركة ');
            frm.set_df_property('to_company', 'label', 'الي فرع ال');
            frm.set_df_property('branch', 'label', 'الفرع (المستقبل)');

            frm.set_df_property('our_profit', 'label', "عمولة الشركة");
            frm.set_df_property('other_party_profit', 'label', 'عمولة الفرع');

            type = 1;
            frm.set_df_property('to_comapny', 'read_only', 1);
            frm.set_df_property('from_company', 'read_only', 0);
            frm.refresh_fields();

        }
        if (frm.doc.select_internal == "من فرع الي شركة") {
            frappe.show_alert("من فرع الي شركة ");

            frm.set_df_property('other_party_profit', 'read_only', 0);

            frm.set_value('from_type', 'Branch');
            frm.set_value('to_type', 'Customer');
            frm.set_df_property('from_company', 'label', 'من فرع');
            frm.set_df_property('to_company', 'label', 'الي شركة ');
            frm.set_df_property('branch', 'label', 'الفرع (المرسل)');


            frm.set_df_property('our_profit', 'label', "عمولة الفرع")
            frm.set_df_property('other_party_profit', 'label', "عمولة الشركة")

            type = 2;

            frm.set_df_property('from_company', 'read_only', 1)
            frm.set_df_property('to_comapny', 'read_only', 0);

            //reset from_company to_company fields

        }

        //clear field for new inputs

        if (frm.select_internal) {
            frm.fields_dict['from_company'].set_value("")
            frm.fields_dict['branch'].set_value("")
            frm.fields_dict['to_company'].set_value("")

            frm.refresh_fields()

        }
    },
    without_profit: function (frm) {
        if(frm.doc.without_profit){
            frm.set_value('our_profit', 0)
            frm.set_value('other_party_profit', 0)
            frm.set_value('profit', 0)
            frm.set_value('profit_is_splited', 0);
            frm.set_df_property('other_party_profit', 'read_only', 1);
            frm.set_df_property('our_profit', 'read_only', 1);
            frm.set_df_property('profit', 'read_only', 1);
            frm.set_df_property('profit_is_splited', 'read_only', 1);
            frm.refresh_fields();
        }
        else{
            frm.set_df_property('other_party_profit', 'read_only', 0);
            frm.set_df_property('our_profit', 'read_only', 0);
            frm.set_df_property('profit', 'read_only', 0);
            frm.set_df_property('profit_is_splited', 'read_only', 0);
            frm.refresh_fields();
        }

    },
    branch: function (frm) {
        if (frm.doc.branch) {
            if (type === 1) {
                frappe.show_alert("من شركة الي فرع")
                frm.set_value('to_company', frm.doc.branch)
                frm.set_df_property('to_comapny', 'read_only', 1)
                frappe.call({
                    method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_temp_account', // Specify your server-side method here
                    args: {
                        branch: frm.doc.branch,

                    },
                    callback: function (r) {
                        if (r.message) {
                            // check if the account is found
                            frm.set_value('profit_account', r.message);
                            frm.set_value('credit', r.message)
                            frm.set_value('debit', "Debtors - A")
                        }
                    },
                    error: function (error) {
                        frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                    }
                });
            }
            else {

                if (type === 2) {
                    frappe.show_alert("من فرع الي شركة")
                    frm.set_value('from_company', frm.doc.branch)
                    frm.set_df_property('from_company', 'read_only', 1)

                    frappe.call({
                        method: 'transfer.transfer.doctype.company_transfer.company_transfer.get_main_account', // Specify your server-side method here
                        args: {
                            branch: frm.doc.branch,

                        },
                        callback: function (r) {
                            if (r.message) {
                                // check if the account is found
                                frm.set_value('profit_account', r.message);
                                frm.set_value('debit', r.message)
                                frm.set_value('credit', "Debtors - A")

                            }
                        },
                        error: function (error) {
                            frappe.msgprint(__('لا يوجد حساب لهذا الفرع'));
                        }
                    });

                }
            }



        }
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
    check_tslmfrommain: function (frm) {
        let prev_debit = frm.doc.credit;
        if (frm.doc.check_tslmfrommain) {
            prv_acc = frm.doc.credit;
            // Define the account index you want to fetch
            let company_main_account_index = 3;  // Change this index as needed, e.g., 0 for the first account, 1 for the second
            let company_main = frappe.get_cached_doc("Transfer Setting").main_branch;
            // Call the Python method to get the account for the selected branch and index
            frappe.call({
                method: "transfer.transfer.api.get_account_for_branch", // Path to the Python method
                args: {
                    branch_name: company_main, // Pass the selected branch name
                    account_index: company_main_account_index       // Pass the account index
                },
                callback: function (r) {
                    console.log('Account response:', r.message); // Log the response for debugging

                    if (r.message) {
                        // Set the account from the response to the fbfbfb field
                        frm.set_value('credit', r.message);
                        frm.set_value('profit_account', r.message);

                        frm.refresh_field('credit');
                        //frappe.msgprint(__('Account for branch {0} is {1}', 
                        //[frm.doc.from_branch, r.message]));
                    } else {
                        // Clear the fbfbfb field if no account is found

                        frm.refresh_field('credit');
                        frappe.msgprint(__('No account found for the selected branch.'));
                    }
                },
                error: function (error) {
                    console.error('Error fetching account:', error); // Log any errors
                }
            });

        } else {
            // Clear the fbfbfb field if no branch is selected

        }


    }

});

function reset_fields(frm) {
    frm.set_value("branch", "");
    frm.set_value("from_company", "");
    frm.set_value("to_company", "");
    frm.set_value("profit_account", "");
    frm.set_value("debit", "");
    frm.set_value("credit", "");
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

