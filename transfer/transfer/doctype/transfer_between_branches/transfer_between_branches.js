// Copyright (c) 2024, a and contributors
// For license information, please see license.txt


frappe.ui.form.on('transfer between branches', {
    refresh: function(frm) {
        // Check if the document is in the "غير مستلمة" workflow state
        if (frm.doc.docstatus === 1  ) {

            // Calculate the time difference in hours between document creation and the current time
            const creation_time = new Date(frm.doc.creation);
            const current_time = new Date();
            const time_diff = (current_time - creation_time) / (1000 * 3600); // Convert milliseconds to hours

            if (time_diff <= 24) {
                // Add "Reverse" button for documents created more than 24 hours ago
                frm.add_custom_button(__('عكس الحوالــة'), function() {
                    frappe.call({
                        method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.handel_cancelation',
                        args: {
                            docname: frm.doc.name,
                            method: "reversal"
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Document has been reversed successfully.'));
                                frm.reload_doc(); // Reload to reflect changes
                            }
                        }
                    });
                });
            } else {
                // Add "إلغاء الحوالة" button for documents created less than 24 hours ago
                frm.add_custom_button(__('إلغاء الحوالة'), function() {
                    frappe.call({
                        method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.handel_cancelation',
                        args: {
                            docname: frm.doc.name,
                            method: "cancel"
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Document has been canceled successfully.'));
                                frm.reload_doc(); // Reload to reflect changes
                            }
                        }
                    });
                });
            }
        }
    }
});

frappe.ui.form.on('transfer between branches', {
	refresh: function(frm) {
    
        // Add a custom button for workflow_state "تم التسليم"
      

			frm.add_custom_button(__('حــذف نهائي'), function () {
				frappe.confirm(
					'هل انت متاكد ?',
					function () {
						// Call the server-side method to delete the current document
						frappe.call({
							method: 'transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.delete_current_doc',
							args: {
								docname: frm.doc.name,
								method : "submit"
							},
							callback: function (response) {
								if (response.message.status === 'success') {
									frappe.msgprint(response.message.message);
									frappe.set_route('List', 'transfer between branches');
								} else {
									frappe.msgprint({
										title: __('Error'),
										message: response.message.message,
										indicator: 'red'
									});
								}
							}
						});
					}
				);
			});
		   }
	});

	frappe.ui.form.on('transfer between branches', {
		from_branch: function(frm) {
			if (frm.doc.from_branch) {
				console.log('Selected branch:', frm.doc.from_branch,frm.doc.to_branch); // Log the selected branch
	
				// Define the account index you want to fetch
				let accountIndex = 0;  // Change this index as needed, e.g., 0 for the first account, 1 for the second
	
				// Call the Python method to get the account for the selected branch and index
				frappe.call({
					method: "transfer.transfer.api.get_account_for_branch", // Path to the Python method
					args: {
						branch_name: frm.doc.from_branch, // Pass the selected branch name
						account_index: accountIndex       // Pass the account index
					},
					callback: function(r) {
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
					error: function(error) {
						console.error('Error fetching account:', error); // Log any errors
					}
				});
			} else {
				// Clear the fbfbfb field if no branch is selected
				frm.set_value('debit', null);
				frm.refresh_field('debit');
			}
		},
		to_branch: function(frm) {
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
					callback: function(r) {
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
					error: function(error) {
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
		on_submit:function (frm) {
			frappe.show_alert({ message: __("Document has been submitted successfully"), indicator: "green" });
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
			callback: function(response) {
				if (!response.exc) {
					frappe.show_alert({ message: __("Action completed successfully"), indicator: "green" });
				}
			}
			
		});
	}
//toggle select field
// frappe.ui.form.on('transfer between branches', {
//         refresh: function(frm) {
//             // Ensure the state of the select field is correct on form load
//             toggle_select_field(frm);
//         },
//         from_branch: function(frm) {
//             // Trigger when 'from_branch' is changed
//             toggle_select_field(frm);
//         },
//         to_branch: function(frm) {
//             // Trigger when 'to_branch' is changed
//             toggle_select_field(frm);
//         }
//     });
	
	// Custom function to enable/disable the select field
//     function toggle_select_field(frm) {
//         if (frm.doc.from_branch && frm.doc.to_branch) {
//             // Enable the select field if both are filled
//             frm.set_df_property('status', 'read_only', 0); // Replace 'status' with your select field name
//         } else {
//             // Disable the select field if either is empty
//             frm.set_df_property('status', 'read_only', 1);
//         }
//     }

//disable profit amount
frappe.ui.form.on('transfer between branches', {
		without_profit: function(frm) {
			if (frm.doc.without_profit) {
				frm.set_value('profit',0); // Clear the amount field when checkbox is checked
				//frappe.msgprint(__('Amount field value: {0}', [frm.doc.profit]));
				frm.set_value('check_without_profit',0);
			}
		}, 
		check_without_profit: function(frm) {
			if (frm.doc.check_without_profit) {
				//frappe.msgprint(__('Amount field value: {0}', [frm.doc.profit]));
				frm.set_value('without_profit',0);
			}
		}

	});

//profit calcualtion


frappe.ui.form.on('transfer between branches', {
		amount: function(frm) {
			calculate_profit(frm);
		},
		profit_per_thousand: function(frm) {
			calculate_profit(frm);
		}
	});
	
	function calculate_profit(frm) {
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
			frm.set_value('profit', profit);
			console.log('Calculated Profit:', profit); // Log the calculated profit for debugging
		}
	}
	

