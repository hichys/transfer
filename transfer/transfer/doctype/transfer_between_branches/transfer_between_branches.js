
frappe.ui.form.on('transfer between branches', {

	before_workflow_action: async (frm) => {
		// console.log("Triggered before_workflow_action");
		frappe.dom.unfreeze();
		if (frm.doc.workflow_state === "غير مستلمة" && frm.selected_workflow_action === "تم التسليم") {
			try {
				// Display the confirmation dialog
				let userConfirmed = await new Promise((resolve) => {
					frappe.confirm(

						__("هل انت متاكد من التسليم قد تم ؟"),
						() => {
							// User clicked "Yes"
							resolve(true);
						},
						() => {
							// User clicked "No"
							resolve(false);
						}
					);
				});

				if (!userConfirmed) {
					// Stop the workflow by throwing an error
					frappe.show_alert(__("تم الإلغاء"));
					throw new Error("Workflow action cancelled by user.");
				}

			} catch (error) {
				throw error; // Ensure workflow doesn't proceed
			}
		}
		if (frm.selected_workflow_action === "إلغاء الحوالة") {
			return new Promise(async (resolve, reject) => {
				try {
					const userConfirmed = await new Promise((confirmResolve) => {
						frappe.confirm(
							__("هل انت متأكد من إلغاء الحوالة؟ سيتم أيضًا إلغاء قيود اليومية المرتبطة."),
							() => confirmResolve(true),
							() => confirmResolve(false)
						);
					});

					if (!userConfirmed) {
						frappe.show_alert({ message: __('تم إلغاء الإجراء'), indicator: 'yellow' });
						reject(new Error('Cancellation aborted by user'));
						return;
					}

					// Check if created today and handle accordingly
					await handelCancelAction(frm);

					resolve(); // Resolve the promise if everything succeeded

				} catch (error) {
					reject(error); // Reject if any error occurred
				}
			});
		}
		else {
			console.log("Conditions not met. No confirmation required.");
		}
	},

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
                                        <p><strong>الكود:</strong> ${frm.doc.name}</p>
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
								method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.manual_submit',
								args: { docname: frm.doc.name },
								callback: function (r) {
									dialog.hide();

									if (r.message.status === 'success') {
										frappe.show_alert(__('تم التسجيل'));
										frm.reload_doc();
									}
									else {
										let error_msg = r.message?.message || __('فشل في التسجيل');
										frappe.show_alert({ message: error_msg, indicator: 'red' });
									}
								},
								error: function (err) {
									$dialog.hide();
									frappe.msgprint(__('حدث خطأ في الشبكة الرجاء تحديث الصفحه'));
									console.error(err);
								},


							});

						}
					});

					// Show the dialog
					dialog.show();

					// Add "copy details" functionality
					dialog.$wrapper.on('click', '#copy-details', function () {
						const detailsText = `
						الكود: ${frm.doc.name}
						المرسل: ${details.from_company}
						المستقبل: ${details.to_company}
						القيمة: ${details.amount}
						عمولة ${details.from_company}: ${details.profit}
						عمولة ${details.to_company}: ${details.other_party_profit}
					`;

						if (navigator.clipboard && navigator.clipboard.writeText) {
							navigator.clipboard.writeText(detailsText).then(() => {
								frappe.show_alert('تم نسخ التفاصيل إلى الحافظة.');
							}).catch(err => {
								frappe.msgprint('حدث خطأ أثناء نسخ النص.');
								console.error(err);
							});
						} else {
							// fallback for insecure contexts
							let textarea = document.createElement("textarea");
							textarea.value = detailsText;
							document.body.appendChild(textarea);
							textarea.select();
							try {
								document.execCommand('copy');
								frappe.show_alert('تم نسخ التفاصيل .');
							} catch (err) {
								frappe.msgprint('حدث خطأ أثناء نسخ النص .');
							}
							document.body.removeChild(textarea);
						}
					});

				}
			}
		});
	}
});

frappe.ui.form.on('transfer between branches', {

	validate: function (frm) {
		///ensure that the amount is greater than 0
		if (frm.doc.amount <= 0) {
			frappe.msgprint({
				title: __('خطا'),
				message: __('الرجاء ادخال قيمة اكبر من صفر'),
				indicator: 'red'
			});
			frm.set_value('amount', 0);
			frm.refresh_field('amount');
			frappe.validated = false;
		}
		// Ensure that out_profit and other_party_profit are greater is equal to total_profit
		if (frm.doc.our_profit + frm.doc.other_party_profit !== frm.doc.total_profit) {
			frm.set_value('our_profit', 0);
			frm.set_value('other_party_profit', 0);
			frm.refresh_field('our_profit');
			frm.refresh_field('other_party_profit');
			frappe.throw("الرجاء التأكد من ادخال العمولة بشكل صحيح");

			frappe.validated = false;
		}

	},
	onload: function (frm) {
		//retrieve profit_per_thousand from transfer setting doctype
		if (frm.is_new()) {
			frappe.db.get_single_value("transfer setting", "profit_per_thousand").then(value => {
				frm.doc.profit_per_thousand = value;
				frm.refresh_field('profit_per_thousand');
			});
		}
		
	},
	refresh: function (frm) {
		loadButtons(frm);

		//set filter so that to and from branch cant be the same
		frm.set_query("from_branch", function () {
			return {
				filters: [
					["name", "!=", frm.doc.to_branch]
				]
			};
		});
		frm.set_query("to_branch", function () {
			return {
				filters: [
					["name", "!=", frm.doc.from_branch]
				]
			};
		});


		if (frm.total_profit === 0 || !frm.total_profit) {
			frm.set_df_property("split_profit", "read_only", 1);
		}

		if (frm.doc.to_branch && frm.doc.from_branch && frm.doc.to_branch != null && frm.doc.from_branch != null) {
			if (frm.doc.to_branch === frm.doc.from_branch) {
				frappe.msgprint({
					title: __('خطا'),
					message: __('لا يمكن نقل الحوالة الى نفس الفرع'),
					indicator: 'red'
				});
				frm.set_value('to_branch', null);
				frm.refresh_field('to_branch');
			}
		}

	},
});
frappe.ui.form.on('transfer between branches', {
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
	from_branch: function (frm) {
		if (frm.doc.from_branch) {
			// console.log('Selected branch:', frm.doc.from_branch, frm.doc.to_branch); // Log the selected branch

			// Define the account index you want to fetch
			let accountIndex = 0;  // Change this index as needed, e.g., 0 for the first account, 1 for the second

			// Call the Python method to get the account for the selected branch and index
			frappe.call({
				method: "transfer.transfer.api.get_account_for_branch", // Path to the Python method
				args: {
					branch_name: frm.doc.from_branch, // Pass the selected branch name
					account_index: accountIndex       // Pass the account index
				},
				callback: function (r) {
					// console.log('Account response:', r.message); // Log the response for debugging

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
			frm.set_value('debit', null);
			frm.refresh_field('debit');
		}
	},
	to_branch: function (frm) {

		if (frm.doc.to_branch) {

			// console.log('Selected branch:', frm.doc.to_branch); // Log the selected branch

			// Define the account index you want to fetch
			let accountIndex = 1;  // Change this index as needed, e.g., 0 for the first account, 1 for the second

			// Call the Python method to get the account for the selected branch and index
			frappe.call({
				method: "transfer.transfer.api.get_account_for_branch", // Path to the Python method
				args: {
					branch_name: frm.doc.to_branch, // Pass the selected branch name
					account_index: accountIndex       // Pass the account index
				},
				callback: function (r) {
					// console.log('Account response:', r.message); // Log the response for debugging

					if (r.message) {
						// Set the account from the response to the fbfbfb field
						frm.set_value('credit', r.message);
						frm.refresh_field('credit');
						//frappe.msgprint(__('Account for branch {0} is {1}', 
						// [frm.doc.to_branch, r.message]));
					} else {
						// Clear the fbfbfb field if no account is found
						frm.set_value('credit', null);
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
			frm.set_value('credit', null);
			frm.refresh_field('credit');
		}
	},
	amount: function (frm) {
		var valid = validate_float_fields(frm.doc.amount);

		if (valid) {
			calculate_profit(frm);
		}

		frm.trigger('split_profit')


	},
	total_profit: function (frm) {

		// frm.trigger('profit_per_thousand');

		if (frm.doc.total_profit > 0) {
			frm.set_df_property("split_profit", "read_only", 0);
			frm.refresh_field('split_profit')
		}
		var valid = validate_float_fields(frm.doc.total_profit);
		if (valid) {
			adjust_profits(frm, 'total_profit');
		}
		frm.set_value('our_profit', frm.doc.total_profit);
		frm.trigger('split_profit');


	},
	our_profit: function (frm) {
		var valid = validate_float_fields(frm.doc.our_profit);
		if (valid) {
			adjust_profits(frm, 'our_profit');
		}
		if (frm.doc.our_profit !== frm.doc.other_party_profit) {
			frm.set_value('split_profit', 0);
		}
		else {
			frm.set_value('split_profit', 1);
		}


	},
	other_party_profit: function (frm) {
		var valid = validate_float_fields(frm.doc.other_party_profit);
		if (valid) {
			adjust_profits(frm, 'other_party_profit');
		}
		if (frm.doc.our_profit !== frm.doc.other_party_profit) {
			frm.set_value('split_profit', 0);
		}
		else {
			frm.set_value('split_profit', 1);
		}
	},
	profit_per_thousand: function (frm) {

		if (frm.doc.profit_per_thousand === 0) {
			frm.trigger('without_profit');
		}
		else {
			var valid = validate_float_fields(frm.doc.profit_per_thousand);
			if (!valid) {
				profit_per_thousand = 0;
				frm.set_value('profit_per_thousand', 0);
				frm.refresh_field('profit_per_thousand');
			}

			// calculate_profit(frm);
			adjust_profits(frm, 'profit_per_thousand')
		}


	},
	without_profit: function (frm) {
		// 0 the profit fields if without_profit is checked
		// uncheck split profit
		// check without profit
		if (frm.doc.without_profit || frm.doc.profit_per_thousand === 0) {
			frm.set_value('our_profit', 0);
			frm.set_value('other_party_profit', 0);
			frm.set_value('total_profit', 0);
			frm.set_value('profit_per_thousand', 0);
			frm.set_value('split_profit', 0);
		}

	},
	split_profit: function (frm) {


		if (frm.doc.split_profit) {

			frm.set_value('without_profit', 0);
			//split profit
			if (frm.doc.split_profit && frm.doc.total_profit >= 0) {

				//recalculate profit
				var original_profit = calculate_profit(frm);
				frm.set_value('our_profit', original_profit / 2);
				frm.set_value('other_party_profit', original_profit / 2);
				frappe.show_alert({ message: 'العمولة مقسومة' + ': ' + frm.doc.our_profit, indicator: 'green' });

			}
			else {
				if (frm.doc.split_profit && frm.doc.profit < 0) {
					frappe.show_alert({ message: 'Profit must be greater than 0', indicator: 'red' });
				}
			}

		}
	},
	check_tslmfrommain: function (frm) {
		let prev_debit = frm.doc.debit;
		if (frm.doc.check_tslmfrommain) {
			let company_main_account_index = 3;  // Change this index as needed, e.g., 0 for the first account, 1 for the second
			let company_main = "";
			frappe.get_cached_doc("transfer setting", "main_branch").then(value => {
				company_main = value;
				// console.log('Main branch from settings:', company_main);
				if (!company_main) {
					frappe.msgprint(__('Main branch is not set in Transfer Setting'));
					frm.set_value('check_tslmfrommain', 0);
					frm.refresh_field('check_tslmfrommain');
					return;
				}
				frappe.call({
					method: "transfer.transfer.api.get_account_for_branch", // Path to the Python method
					args: {
						branch_name: company_main, // Pass the selected branch name
						account_index: company_main_account_index       // Pass the account index
					},
					callback: function (r) {
						// console.log('Account response:', r.message); // Log the response for debugging

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
			});
		} else {
			// Clear the fbfbfb field if no branch is selected
			frm.set_value('debit', prev_debit);
			frm.refresh_field('debit');
		}
	},
	phone_number: function (frm) {
		if (frm.doc.phone_number) {
			let today = frappe.datetime.get_today(); // format: YYYY-MM-DD
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "transfer between branches",
					filters: [
						["phone_number", "=", frm.doc.phone_number],
						["name", "!=", frm.doc.name],
						["posting_date", "between", [
							today + " 00:00:00",
							today + " 23:59:59"
						]]
					],
					fields: ["phone_number"],
				},
				callback: function (r) {
					if (r.message && r.message.length > 1) {
						frappe.show_alert({
							message: `⚠️ ${r.message.length} record(s) created today with this phone number`,
							indicator: 'green'
						});
					}
				}
			});
		}
	},
	whatsapp_desc: function (frm) {
		clearTimeout(frm.delayTimeout);
		if (frm.doc.whatsapp_desc && !frm.doc.phone_number) {
			frm.delayTimeout = setTimeout(() => {
				let phoneNumber = extract_phone_number(frm.doc.whatsapp_desc);
				if (phoneNumber !== "ادخل يدويا") {
					frm.set_value("phone_number", phoneNumber);
				} // Set the phone number field
				frappe.show_alert({
					message: phoneNumber === "ادخل يدويا" ? "لا يمكن استخراج الرقم. ادخله يدوياً" : `تم استخراج الرقم: ${phoneNumber}`,
					indicator: phoneNumber === "ادخل يدويا" ? "red" : "green"
				});
			}, 1000);
		}
	}
});

function calculate_profit(frm) {

	if (frm.doc.profit_per_thousand === 0) {
		frm.set_value('without_profit', 1);
		frm.set_value('split_profit', 0);
		return 0;
	}
	else
		if (frm.doc.profit_per_thousand === 0 && frm.doc.amount === 0) {
			frm.set_value('without_profit', 1);
			frm.set_value('split_profit', 0);
			return 0;
		}

	if (frm.doc.amount && frm.doc.profit_per_thousand) {
		let profit = 0;

		if (frm.doc.amount < 1100) {
			profit = frm.doc.profit_per_thousand; // Fixed profit if amount is less than 1100
		} else {
			// Calculate profit for amounts >= 1100
			let rounded_amount = Math.ceil(frm.doc.amount / 1000); // Round up to nearest 1000
			profit = rounded_amount * frm.doc.profit_per_thousand; // Use profit_per_thousand for calculation
		}

		// Set the calculated profit in the profit field
		frm.set_value('total_profit', profit);
		frm.set_value('other_party_profit', 0);
		return profit;
	}
	else {
		frm.set_value('total_profit', 0);

	}
}
function calculate_profit_per_thousand(frm) {
	if (!frm.doc.total_profit || !frm.doc.amount || frm.doc.amount === 0) {
		return 0;
	}

	if (frm.doc.total_profit === 0) {
		return 0;
	}

	let profit_per_thousand = 0;

	if (frm.doc.amount < 1100) {
		// For amounts less than 1100, profit_per_thousand equals total_profit
		profit_per_thousand = frm.doc.total_profit;
	} else {
		// For amounts >= 1100, reverse the calculation
		let rounded_amount = Math.ceil(frm.doc.amount / 1000);
		profit_per_thousand = frm.doc.total_profit / rounded_amount;
	}

	return profit_per_thousand;
}
function validate_float_fields(value) {
	// Validate the amount and profit_per_thousand fields

	const floatRegex = /^-?\d+(\.\d+)?$/;
	if (!floatRegex.test(value)) {
		frappe.msgprint({
			title: __('خطا'),
			message: __('الرجاء ادخال قيمة صحيحة'),
			indicator: 'red'
		});
		frm.set_value('amount', 0);
		return false;
	}

	if (value < 0) {
		frappe.msgprint({
			title: __('خطا'),
			message: __('الرجاء ادخال قيمة اكبر من صفر'),
			indicator: 'red'
		});
		frm.set_value('amount', 0);
		return false;
	}

	return true;
}


function adjust_profits(frm, changed_field) {
	const profit = frm.doc.total_profit || 0;
	let our_profit = frm.doc.our_profit || 0;
	let other_party_profit = frm.doc.other_party_profit || 0;

	// Adjust the other field to ensure the total equals profit
		
	if (changed_field === 'total_profit') {
		frm.set_value('profit_per_thousand', calculate_profit_per_thousand(frm));
	}
	else if (changed_field === 'profit_per_thousand') {
		let rounded_amount = Math.ceil(frm.doc.amount / 1000); // Round up to nearest 1000
		const profit = rounded_amount * frm.doc.profit_per_thousand; 
		// console.log(profit)
		frm.set_value('total_profit', profit)
	}
	else if (changed_field === 'our_profit') {
		other_party_profit = profit - our_profit;
		if (other_party_profit < 0) {
			other_party_profit = 0;
			our_profit = profit;
		}


		// Prevent invalid adjustments
		if (other_party_profit < 0 && profit >= 0) {
			frappe.show_alert("The other party's profit cannot be negative when total profit is positive.");
			other_party_profit = 0;
			our_profit = profit;
		} else if (other_party_profit > 0 && profit < 0) {
			frappe.show_alert("The other party's profit cannot be positive when total profit is negative.");
			other_party_profit = 0;
			our_profit = profit;
		}
	} else if (changed_field === 'other_party_profit') {
		our_profit = profit - other_party_profit;

		// Prevent invalid adjustments
		if (our_profit < 0 && profit >= 0) {
			frappe.show_alert("Our profit cannot be negative when total profit is positive.");
			our_profit = 0;
			other_party_profit = profit;
		} else if (our_profit > 0 && profit < 0) {
			frappe.show_alert("Our profit cannot be positive when total profit is negative.");
			our_profit = 0;
			other_party_profit = profit;
		}
	}

	// Update the fields
	frm.set_value('our_profit', our_profit);
	frm.set_value('other_party_profit', other_party_profit);

	// Refresh fields to reflect changes
	frm.refresh_fields();
}


function loadButtons(frm) {
	if (frm.doc.docstatus === 0 && !frm.is_new() && frm.doc.workflow_state === "غير مسجلة") {
		frm.add_custom_button(__('تسجيل'), function () {
			frm.trigger('create_journal_entry');
		});
	}
	else {
		// If the document is saved or in any other workflow state, don't show the button
		frm.remove_custom_button(__('تسجيل'));
	}

	if (frm.doc.workflow_state == 'غير مستلمة') {
		frm.add_custom_button(__('تم التسليم'), function () {
			// Create a new dialog instance
			let dialog = new frappe.ui.Dialog({
				title: __('تأكيد'), // Title of the dialog
				fields: [], // You can add fields here if needed
				primary_action_label: __('نعم، تم التسليم'), // Your custom "Yes" button label
				secondary_action_label: __('لا، إلغاء'), // Your custom "No" button label
				primary_action(values) {
					// This function is executed when the custom "Yes" button is clicked
					frappe.call({
						method: "frappe.model.workflow.apply_workflow",
						args: {
							doc: frm.doc,
							action: "تم التسليم" // The workflow action name
						},
						callback: function (r) {
							if (!r.exc) {
								frappe.show_alert(__('تمت العملية بنجاح'));
								frm.reload_doc();
							}
						}
					});
					dialog.hide();
				},
				secondary_action(values) {
					// This function is executed when the custom "No" button is clicked
					frappe.show_alert("تم الإلغاء");
					dialog.hide();
				}
			});

			// Show the custom dialog to the user
			dialog.show();

		});
	}
	if (frm.doc.docstatus === 2) {
		//delete_doc_with_linked_js
		// if (frm.doc.workflow_state == 'ملغية') {
		// 	frm.add_custom_button(__('مسح'), function () {
		// 		frappe.call({
		// 			method: "transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.delete_doc_with_links",
		// 			args: {
		// 				doctype: frm.doc.doctype,
		// 				docname: frm.doc.name
		// 			},
		// 			callback: function () {
		// 				frappe.msgprint(__('Document deleted'));
		// 				frappe.set_route('List', frm.doc.doctype);
		// 			}
		// 		});
		// 	}, 'Actions');
		// }
	}
}

function handelCancelAction(frm) {
	const cancel_method = is_created_today(frm.doc.posting_date) ? "cancel" : "reversal";
	const cancel_msg = cancel_method === "cancel" ? "إلغاء" : "عكس";
	return new Promise((resolve, reject) => {
		frappe.call({
			method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.handel_cancelation',
			args: {
				docname: frm.doc.name,
				method: cancel_method
			},
			callback: function (r) {
				if (!r.exc) {
					frappe.show_alert({ message: __('تم {0} الحوالة بنجاح', [cancel_msg]), indicator: 'green' });
					frm.reload_doc(); // Reload to reflect changes
					resolve(true);
				} else {
					// Show error message if there's an exception
					frappe.msgprint({
						title: __('Error'),
						message: __('فشل في إلغاء الحوالة: ') + (r.exc || __('خطأ غير معروف'))
					});
					reject(r.exc);
				}
			},
			error: function (err) {
				// Handle network/connection errors
				frappe.msgprint({
					title: __('Network Error'),
					message: __('حدث خطأ في الشبكة. يرجى المحاولة مرة أخرى.')
				});
				console.error(err);
				reject(err);
			}
		});
	});
}
function is_created_today(posting_date) {
	const creation_date = new Date(posting_date);
	const current_date = new Date();

	// Strip time from both dates by setting the time to midnight (00:00)
	creation_date.setHours(0, 0, 0, 0);
	current_date.setHours(0, 0, 0, 0);

	// Calculate the difference in milliseconds
	const day_diff = (current_date - creation_date) / (1000 * 3600 * 24); // Convert milliseconds to days

	return day_diff <= 1;
}