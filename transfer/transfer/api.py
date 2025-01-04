import frappe
from frappe.model.document import Document

@frappe.whitelist()
def get_currency_remaining_qty(currency):
	total_sold_qty = 0
	total_remaining_qty = 0

	# Get all draft or submitted Sales Invoices with the specified currency
	sales_invoices = frappe.get_all(
		'Sales Invoice',
		filters={'currency': currency, 'docstatus': ['<', 2]},  # Draft and submitted invoices
		fields=['name']
	)

	# Fetch sold quantities from the Sales Invoice Item
	for invoice in sales_invoices:
		items = frappe.get_all(
			'Sales Invoice Item',
			filters={'parent': invoice.name},
			fields=['qty', 'item_code']
		)
		for item in items:
			total_sold_qty += item.qty  # Sum the quantities sold

			# Now, check the stock for the same item in the warehouse
			# Assuming the stock is tracked in the Bin table for each item and warehouse
			stock_bin = frappe.get_all(
				'Bin',
				filters={'item_code': item.item_code},  # Get stock info for the item
				fields=['actual_qty', 'reserved_qty', 'indented_qty']  # Adjust based on your stock fields
			)

			# Calculate the remaining quantity in the warehouse
			remaining_qty_in_warehouse = 0
			for bin in stock_bin:
				# Subtract reserved or indented quantities from actual stock if needed
				remaining_qty_in_warehouse += (bin.actual_qty )

			total_remaining_qty  = remaining_qty_in_warehouse

	# Calculate the remaining quantity (sold - remaining in warehouse)
	remaining_qty = total_remaining_qty - total_sold_qty
	return remaining_qty


@frappe.whitelist()
def get_account_for_branch(branch_name, account_index=0):
	# Convert account_index to integer (in case it's passed as a string)
	
	try:
		account_index = int(account_index)

	# Fetch the BranchAccounts document by its name
		branch_account_doc = frappe.get_doc('BranchAccounts', branch_name)
		
		if branch_account_doc:
			# Access the child table 'accounts' (which uses the 'Branch Account Mapping' DocType)
			accounts = branch_account_doc.accounts
			
			# Check if the requested account index is within the valid range
			if len(accounts) > account_index:
				# Return the account at the specified index
				return accounts[account_index].get('account')  # Ensure 'account' is the correct field name
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in get_account_for_branch")
		frappe.throw(f"An error occurred while fetching the account: {str(e)}")

	return False
#canel journal entry
@frappe.whitelist()
def cancel_journal_entery(self,docname):
	# Fetch the original journal entry using the 'cheque_no' as the reference to self.name
	journal_entry = frappe.get_doc("Journal Entry", self.name)
	

@frappe.whitelist()
def reverse_journal_entry(self,docname):
	try:
		# Fetch the original journal entry using the 'cheque_no' as the reference to self.name
		journal_entry = frappe.get_doc("Journal Entry", self.name)
		if journal_entry:
			# Get the original journal entry
			 
			# Prepare reversed accounts by swapping the debit and credit values
			reversed_accounts = []
			for account in journal_entry.accounts:
				reversed_account = {
					"account": account.account,
					"branch": account.branch,
					"party_type": account.party_type,
					"party": account.party,
					"debit_in_account_currency": account.credit_in_account_currency,
					"credit_in_account_currency": account.debit_in_account_currency,
				}
				reversed_accounts.append(reversed_account)
				
			# Create the reversed journal entry
			reversed_je = frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": journal_entry.voucher_type,
				"posting_date": nowdate(),
				"company": journal_entry.company,
				"accounts": reversed_accounts,
				"mode_of_payment": "Cash",  # Adjust as per your requirements
				"cheque_no": f"{docname}",
				"cheque_date": nowdate(),
				"reversal_of": journal_entry.name
			})
			
			# Insert and submit the reversed journal entry
			reversed_je.insert(ignore_permissions=True)
			reversed_je.submit()

			#edit original journal entry
			journal_entry.custom_reversed_by = reversed_je.name
			journal_entry.save()
			frappe.db.commit()
			frappe.msgprint(f"Journal Entry {reversed_je.name} has been reversed successfully.")

			return {
				"status": "success",
				"journal_entry": reversed_je.name
			}

		else:
			frappe.throw(f"No journal entry found for the provided cheque number: {self.name}")
	
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in Reversing Journal Entry")
		frappe.throw(f"An error occurred while reversing the Journal Entry: {str(e)}")

#الحساب الرئيسي
@frappe.whitelist()
def get_main_account(branch):
	return get_account_for_branch(branch,0);
@frappe.whitelist()
#معلقات
def get_profit_account(branch):
	return get_account_for_branch(branch,1);
#ارباح
@frappe.whitelist()
def get_temp_account(branch):
	return get_account_for_branch(branch,2);

