# Copyright (c) 2025, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from transfer.transfer.api import get_account_for_branch,get_main_account,get_profit_account,get_temp_account
from frappe.utils import getdate, nowdate


class InternalTransfer(Document):
	pass




@frappe.whitelist()
def handel_journal_entries_creation(docname):
	doc = frappe.get_doc("Internal Transfer",docname)

	#بدون تعليق الحوالة
	if doc.select_internal == "من فرع الي شركة":
		frappe.msgprint("handel journal enteris من فرع الي شركة")
		create_journal_entry(doc,temp=False)
	#الحوالة تعلق لين تستلم
	if doc.select_internal == "من شركة الي فرع" :
		frappe.msgprint("#######")
		create_journal_entry(doc,temp=True)

@frappe.whitelist()
def create_journal_entry(self,temp=False):
	
	profit = self.our_profit
	profit_account = get_profit_account(self.branch)

	debit = self.debit
	credit = self.credit

	branch = self.branch
	our_profit = self.our_profit
	other_party_profit = self.other_party_profit
	amount = self.amount + other_party_profit
	from_party_name = self.from_company
	to_party_name = self.to_company
	
	try:
		journal_entries = frappe.get_all("Journal Entry", filters={"cheque_no": self.name})
		if journal_entries:
			frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
			frappe.throw(f"الحوالة مسجلة مسبقا ")
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
		frappe.throw(f"An error occurred while creating the Journal Entry: {str(e)}")
	try:
		# Validate that the required fields are provided

		if not (debit and credit and profit_account):
			frappe.throw("Debit, Credit, and Profit Account must be specified.")


		to_type = ""
		to_party_type = ""
		from_type = ""
		from_party_type = ""

		debit_in_account_currency = 0
		credit_in_account_currency = 0

		if(self.from_type == "Customer"):
			from_type = "Customer"
			from_party_type = from_party_name
			to_type = ""
			to_party_type = ""
			debit_in_account_currency =  amount + our_profit
			credit_in_account_currency = amount  
		else :
			if(self.to_type == "Customer" and self.from_type != "Customer"):
				to_type = "Customer"
				to_party_type = to_party_name
				debit_in_account_currency =  amount + our_profit + other_party_profit
				credit_in_account_currency = amount  + other_party_profit  
				from_type = ""
				from_party_type = ""
	 
			
			
		# Prepare accounts for the Journal Entry
		accounts = [
			{
				"account": self.debit,  # Specify the debit account
				"branch": branch,
				"party_type": from_type,
				"party": from_party_type,
				"debit_in_account_currency": debit_in_account_currency,
				"credit_in_account_currency": 0,
			},
			{
				"account": self.credit,  # Specify the credit account
				"branch": branch,
				"party_type": to_type,
				"party": to_party_type,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": credit_in_account_currency,
			}
		]
		# Add an entry for out_proft if not 0
		if our_profit != 0:
			accounts.append({
				"account": profit_account,
				"branch": branch,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": our_profit,
			})	
		# Add an entry for other_party_profit if not 0
	 


		# Construct the Journal Entry document
		journal_entry = frappe.get_doc({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"posting_date": self.posting_date,
			"accounts": accounts,
			"mode_of_payment": "Cash",
   			"cheque_no": self.name,
			"cheque_date": frappe.utils.nowdate(),

		})

		# Save and Submit the Journal Entry
		journal_entry.insert(ignore_permissions=True)
		journal_entry.submit()
		self.journal_entry = journal_entry.name

		frappe.msgprint(f"Journal Entry {journal_entry.name} created successfully.")

		return {
			"status": "success",
			"journal_entry": journal_entry.name
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
		frappe.throw(f"An error occurred while creating the Journal Entry: {str(e)}")
 

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