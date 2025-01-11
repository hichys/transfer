import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
from datetime import datetime
import re

#get all linked documetns by its cheque_no

@frappe.whitelist()
def get_journal_entries_by_cheque(doc):
    # Fetch the custom document
    
    # Retrieve the related journal entries where the 'cheque_no' matches
    journal_entries = frappe.get_all('Journal Entry', filters={'cheque_no': doc.name}, fields=['name', 'posting_date', 'total_debit', 'total_credit'])
    
    return journal_entries 


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

import frappe
from frappe.utils import nowdate

def create_journal_entry(from_account, to_account, amount,branch=None,cheque_no=None, posting_date=None, remarks=None):
	try:
		# Validate inputs
		if not from_account or not to_account:
			frappe.throw("Both From Account and To Account must be specified.")
		if not amount:
			frappe.throw("Amount must be greater than zero.")
		
		# Use today's date if posting_date is not provided
		posting_date = posting_date or nowdate()
		remarks = remarks or f""

		branch = branch or ""
		cheque_no = cheque_no or ""
		# Create the Journal Entry document

		accounts = [
				{
					"account": from_account,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": amount,
				},
				{
					"account": to_account,
					"credit_in_account_currency": 0,
					"debit_in_account_currency": amount,
				}
			]

		journal_entry = frappe.get_doc({
			"doctype": "Journal Entry",
			"posting_date": posting_date,
			"voucher_type": "Journal Entry",
			"accounts": accounts,
			"user_remark": remarks,
			"branch" : branch,
			"cheque_no": cheque_no,
			"cheque_date": frappe.utils.nowdate(),
		})
		
		# Insert and submit the Journal Entry
		journal_entry.insert()
		journal_entry.submit()
		
		frappe.msgprint(f"Journal Entry {journal_entry.name} created successfully.")
		return journal_entry.name
	
	except Exception as e:
		frappe.throw(f"Error while creating Journal Entry: {str(e)}")


def is_posting_day_today(posting_date):
    return posting_date == datetime.now().date()


#قبل الإلغاء التاكد من ان الجورنال قد لغيت او عكست
def validate_linked_journal_entries(docname, link_fields=["cheque_no"]):
    """
    Validate that all Journal Entries linked to the given document are either canceled,
    reversed (custom_reversed_by set), or have a reversal_of field set.

    Args:
        docname (str): The name of the document being checked.
        link_fields (list): The fields in Journal Entry used to link to the document.

    Raises:
        frappe.ValidationError: If any linked Journal Entries do not meet the required criteria.
    """
    for link_field in link_fields:
        # Fetch all linked Journal Entries
        journal_entries = frappe.get_all(
            "Journal Entry",
            filters={
                link_field: docname,
                "docstatus": ["!=", 2],  # Not canceled
                "custom_reversed_by": ["is", "not set"],  # Not reversed
                "reversal_of": ["is", "not set"]  # Not a reversal
            },
            fields=["name", "docstatus", "custom_reversed_by", "reversal_of"]
        )

        # If any Journal Entries do not meet the criteria
        if journal_entries:
            linked_entries = ", ".join([entry["name"] for entry in journal_entries])
            frappe.throw(
                ("Cannot cancel this document because the following Journal Entries are not canceled or reversed: {0}")
                .format(linked_entries)
            )

# @frappe.whitelist()
# def extract_phone_number(whatsapp_desc):
#     try:
#         # Clean the text to remove spaces and hyphens
#         cleaned_text = whatsapp_desc.replace(" ", "").replace("-", "")  # Remove spaces and hyphens

#         # Match a phone number pattern with or without the country code
#         match = re.match(r'(?:\+?218)?0?(9[1234]\d{7})', cleaned_text)

#         if match:
#             return '0' + match.group(1)  # Return the matched phone number
#         else:
#             return "ادخل يدويا"  # Fallback if no match
#     except Exception as error:
#         print("Error in extract_phone_number:", error)
#         return "ادخل يدويا"  # Fallback for unexpected errors