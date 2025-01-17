// Copyright (c) 2024, a and contributors
// For license information, please see license.txt
let type = 1;
let per_branch = null;
//transfer.transfer.doctype.company_transfer.company_transfer.get_profit_account


frappe.ui.form.on('company transfer', {
    create_journal_entry: function (frm) {
        frappe.call({
            method: 'transfer.transfer.doctype.company_transfer.company_transfer.create_journal_entry_preview',
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
                                method: 'transfer.transfer.doctype.company_transfer.company_transfer.handle_creation',
                                args: { docname: frm.doc.name },
                                callback: function (r) {
                                    if (r.message.status === 'success') {
                                        frappe.show_alert(__('تم التسجيل'));
                                        frm.reload_doc();
                                    }
                                }
                            });
                            dialog.hide();
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

        if (frm.doc.from_company === frm.doc.to_company) {
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

        frappe.realtime.on('doc_update', function (data) {
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
            callback: function (response) {
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
    after_submit: function (frm) {
        frm.reload_doc();
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
    profit_account: function (frm) {


    },
    check_tslmfrommain: function (frm) {
		let prev_debit = frm.doc.debit;
		if (frm.doc.check_tslmfrommain ) {
			// Define the account index you want to fetch
			let company_main_account_index = 3;  // Change this index as needed, e.g., 0 for the first account, 1 for the second
			let company_main = "العالمية الفرناج";
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
						frm.set_value('debit', r.message);
						frm.refresh_field('debit');
						//frappe.msgprint(__('Account for branch {0} is {1}', 
						//[frm.doc.from_branch, r.message]));
					} else {
						// Clear the fbfbfb field if no account is found
						frm.set_value('debit', null);
						frm.refresh_field('debit');
						frappe.msgprint(__('No account found for the selected branch.'));
					}
				},
				error: function (error) {
					console.error('Error fetching account:', error); // Log any errors
				}
			});
		} else {
			// Clear the fbfbfb field if no branch is selected
			frm.set_value('debit', prev_debit);
			frm.refresh_field('debit');
		}
	},
    profit: function (frm) {
        frm.set_value('our_profit', frm.doc.profit);
        frm.set_value('other_party_profit', 0);
        if (frm.doc.profit) {
            frm.set_value("execution_amount", frm.doc.amount + frm.doc.profit)

        }
    },
    select_external: function (frm) {

        if (frm.doc.select_external === "شركات") {
            frm.fields_dict['branch'].set_value(per_branch);
            frm.set_df_property("branch", "read_only", 1);
            frm.fields_dict['from_company'].set_value('');
            frm.set_value("debit", "Debtors - A")

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
                frm.set_value('from_type', "Branch");
                frm.set_value('to_type', "Customer");
                frm.trigger('branch')
                frm.set_df_property("from_company", "read_only", 1);
            }
        }


    },
    from_company: function (frm) {

        //  frm.set_value('debit',"Debtors - A" );
        if (frm.doc.from_company) {
            //  frm.set_value("debit",frm.doc.profit_account) 
        }

    },
    debit: function (frm) {
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
        const profit = execution_amount - amount;

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
                frm.trigger('create_journal_entry');

            });
        }
        // if (frm.doc.docstatus == 0 && frm.doc.status == "غير مسجلة" && !frm.is_new()) {
        //     frm.add_custom_button(__('تسجيل'), function () {
        //         frappe.confirm(
        //             'هل انت متاكد من التسجيل  ؟',
        //             function () {
        //                 // Confirmed action
        //                 frappe.call({
        //                     method: "transfer.transfer.doctype.company_transfer.company_transfer.handle_creation",
        //                     args: {
        //                         docname: frm.doc.name,
        //                         method: "submit"
        //                     },
        //                     callback: function (r) {
        //                         if (!r.exc) {
        //                             // frappe.msgprint("Update successful!");
        //                             frm.reload_doc();
        //                         }
        //                     }
        //                 });
        //             },
        //             function () {
        //                 // Cancelled action
        //                 frappe.msgprint(__('Action cancelled.'));
        //             }
        //         );
        //     });
        // }
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
