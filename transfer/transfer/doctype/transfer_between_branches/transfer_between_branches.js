
frappe.ui.form.on('transfer between branches', {

	before_workflow_action: async (frm) => {
		console.log("Triggered before_workflow_action");
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
					frappe.msgprint(__("تم الإلغاء"));
					throw new Error("Workflow action cancelled by user.");
				}

			} catch (error) {
				throw error; // Ensure workflow doesn't proceed
			}
		} else {
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
								method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.manual_submit',
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
		frappe.db.get_single_value("transfer setting", "profit_per_thousand").then(value => {
			frm.set_value('profit_per_thousand', value);
		});
	},
	refresh: function (frm) {


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

		if (frm.doc.docstatus === 0 && !frm.is_new() && frm.doc.workflow_state === "غير مسجلة") {
			frm.add_custom_button(__('تسجيل'), function () {
				frm.trigger('create_journal_entry');
				frm.reload_doc(); // Reload to reflect changes
			});
		}
		else {
			// If the document is saved or in any other workflow state, don't show the button
			frm.remove_custom_button(__('تسجيل'));  // Optionally remove any previously added button
		}

		// if (frm.doc.docstatus === 0 && !frm.is_new() && frm.doc.workflow_state === "غير مسجلة") {
		// 	frm.add_custom_button(__('تسجيل'), function () {
		// 		frappe.confirm(
		// 			"هل تم استلام المبلغ ؟",
		// 			() => {
		// 				frappe.call({
		// 					method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.manual_submit',
		// 					args: {
		// 						docname: frm.doc.name,
		// 					},
		// 					callback: function (r) {
		// 						if (!r.exc) {
		// 							frappe.msgprint(__('تم التسجيل'));
		// 							frm.reload_doc(); // Reload to reflect changes
		// 						}
		// 					}
		// 				});
		// 			},
		// 			() => {
		// 				frappe.msgprint(__('تم إلغاء الإجراء.'));
		// 			}
		// 		);
		// 	});
		// } else {
		// 	// If the document is saved or in any other workflow state, don't show the button
		// 	frm.remove_custom_button(__('تسجيل'));  // Optionally remove any previously added button
		// }
		// Check if the document is in the "غير مستلمة" workflow state
		if (frm.doc.docstatus === 1) {
			// Get the creation date (posting_date) and strip the time part
			const creation_date = new Date(frm.doc.posting_date);
			const current_date = new Date();

			// Strip time from both dates by setting the time to midnight (00:00)
			creation_date.setHours(0, 0, 0, 0);
			current_date.setHours(0, 0, 0, 0);

			// Calculate the difference in milliseconds
			const day_diff = (current_date - creation_date) / (1000 * 3600 * 24); // Convert milliseconds to days

			// Check if the difference is greater than or equal to 1 day
			if (day_diff >= 1) {
				// Add "Reverse" button for documents created more than 24 hours ago
				frm.add_custom_button(__('عكس الحوالــة'), function () {
					frappe.confirm(
						"هل أنت متأكد أنك تريد عكس الحوالة؟",
						() => {
							frappe.call({
								method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.handel_cancelation',
								args: {
									docname: frm.doc.name,
									method: "reversal"
								},
								callback: function (r) {
									if (!r.exc) {
										frappe.msgprint(__('تم عكس الحوالة بنجاح.'));
										frm.reload_doc(); // Reload to reflect changes
									}
								}
							});
						},
						() => {
							frappe.msgprint(__('تم إلغاء الإجراء.'));
						}
					);
				});
			} else {
				// Add "إلغاء الحوالة" button for documents created less than 24 hours ago
				frm.add_custom_button(__('إلغاء الحوالة'), function () {
					frappe.confirm(
						"هل أنت متأكد أنك تريد إلغاء الحوالة؟",
						() => {
							frappe.call({
								method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.handel_cancelation',
								args: {
									docname: frm.doc.name,
									method: "cancel"
								},
								callback: function (r) {
									if (!r.exc) {
										frappe.msgprint(__('تم إلغاء الحوالة بنجاح.'));
										frm.reload_doc(); // Reload to reflect changes
									}
								}
							});
						},
						() => {
							frappe.msgprint(__('تم إلغاء الإجراء.'));
						}
					);
				});
			}
		}

		if (frm.doc.docstatus === 2) {
			//delete_doc_with_linked_js
			if (frm.doc.workflow_state == 'ملغية') {
				frm.add_custom_button(__('Delete'), function () {
					frappe.call({
						method: "transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.delete_doc_with_links",
						args: {
							doctype: frm.doc.doctype,
							docname: frm.doc.name
						},
						callback: function () {
							frappe.msgprint(__('Document deleted'));
							frappe.set_route('List', frm.doc.doctype);
						}
					});
				}, 'Actions');
			}
		}

	}
});

frappe.ui.form.on('transfer between branches', {
	// refresh: function (frm) {

	// Add a custom button for workflow_state "تم التسليم"


	// frm.add_custom_button(__('حــذف نهائي'), function () {
	// 	frappe.confirm(
	// 		'هل انت متاكد ?',
	// 		function () {
	// 			// Call the server-side method to delete the current document
	// 			frappe.call({
	// 				method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.delete_current_doc',
	// 				args: {
	// 					docname: frm.doc.name,
	// 					method : "submit"
	// 				},
	// 				callback: function (response) {
	// 					if (response.message.status === 'success') {
	// 						frappe.msgprint(response.message.message);
	// 						frappe.set_route('List', 'transfer between branches');
	// 					} else {
	// 						frappe.msgprint({
	// 							title: __('Error'),
	// 							message: response.message.message,
	// 							indicator: 'red'
	// 						});
	// 					}
	// 				}
	// 			});
	// 		}
	// 	);
	// });
	// }
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
			console.log('Selected branch:', frm.doc.from_branch, frm.doc.to_branch); // Log the selected branch

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
			frm.set_value('debit', null);
			frm.refresh_field('debit');
		}
	},
	to_branch: function (frm) {

		if (frm.doc.to_branch) {

			console.log('Selected branch:', frm.doc.to_branch); // Log the selected branch

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
					console.log('Account response:', r.message); // Log the response for debugging

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
	}
});

//create journal entery

frappe.ui.form.on('transfer between branches', {
	// status: function (frm) {
	//     if (frm.doc.docstatus === 1) { // Ensure the document is submitted
	//         frappe.msgprint({
	//             title: __('Status Changed'),
	//             message: __('The status has been updated to {0}', [frm.doc.status]),
	//             indicator: 'blue'
	//         });

	//         // create journal entery based on status change
	//         custom_action_on_status_change(frm);

	//     }
	//     else {
	//         frappe.show_alert({ message: __("Documetns is not Submitted Please submit it first"), indicator: "green" });
	//     }
	// },
	after_save: function (frm) {
		// Reload the document to reflect changes

	},
	on_submit: function (frm) {
		// Reload the document to reflect changes
		//custom_action_on_status_change(frm);

	}
});

function custom_action_on_status_change(frm) {
	// Example: Log the new status
	// console.log(`New Status: ${frm.doc.status}`);

	// Add your custom actions here
	// Example: Call a server-side method
	frappe.call({
		method: "transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.on_status_change",
		args: {
			docname: frm.doc.name,
			from_branch: frm.doc.from_branch,
			to_branch: frm.doc.to_branch
		},
		callback: function (response) {
			if (!response.exc) {
				frappe.show_alert({ message: __("Action completed successfully"), indicator: "green" });
			}
		}

	});
}
frappe.ui.form.on('transfer between branches', {
	amount: function (frm) {
		var valid = validate_float_fields(frm.doc.amount);
		if (valid) {
			calculate_profit(frm);
		}


	},
	total_profit: function (frm) {
		var valid = validate_float_fields(frm.doc.total_profit);
		if (valid) {
			adjust_profits(frm, frm.doc.total_profit);
		}
		frm.set_value('our_profit', frm.doc.total_profit);
	},
	our_profit: function (frm) {
		var valid = validate_float_fields(frm.doc.our_profit);
		if (valid) {
			adjust_profits(frm, 'our_profit');
		}
	},
	other_party_profit: function (frm) {
		var valid = validate_float_fields(frm.doc.other_party_profit);
		if (valid) {
			adjust_profits(frm, 'other_party_profit');
		}
	},
	profit_per_thousand: function (frm) {

		var valid = validate_float_fields(frm.doc.profit_per_thousand);
		if (!valid) {
			profit_per_thousand = 0;
			frm.doc.set_value('profit_per_thousand', 0);
			frm.refresh_field('profit_per_thousand');
		}
		calculate_profit(frm);

	},
	without_profit: function (frm) {
		// 0 the profit fields if without_profit is checked
		// uncheck split profit
		// check without profit
		if (frm.doc.without_profit) {
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
				console.log('Main branch from settings:', company_main);
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
			});
		} else {
			// Clear the fbfbfb field if no branch is selected
			frm.set_value('debit', prev_debit);
			frm.refresh_field('debit');
		}
	},
	whatsapp_desc: function (frm) {
		clearTimeout(frm.delayTimeout);
		if (frm.doc.whatsapp_desc) {
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
	if (changed_field === 'our_profit') {
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
