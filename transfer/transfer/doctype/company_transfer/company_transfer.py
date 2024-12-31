# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from transfer.transfer.api import get_account_for_branch
class companytransfer(Document):
	
	def create_company_transfer():
		frappe.msgprint("Company Transfer Created")
	def before_insert(self):
		if(self.our_profit + self.other_party_profit > self.profit):
			frappe.throw("الرجاء التاكد من قيمة العمولة")
	def before_save(self):
		if self.is_new():
			# This will only run on the first save
			create_journal_entry(self)
			self.status = "غير مستلمة"
   
	def after_cancel(self):
		self.status = "ملغية"
	def on_cancel(self):
		##get journal entry and cancel it
		je = frappe.get_all("Journal Entry", filters={"cheque_no": "Journal Entry", "cheque_no": self.name})
		if je:
			je = frappe.get_doc("Journal Entry", je[0].name)
			je.cancel()
			 
		
   
@frappe.whitelist()
def create_journal_entry(self):
	debit = self.amount
	credit = self.execution_amount
	profit = self.profit
	out_proft = self.our_profit
	profit_account = get_account_for_branch(self.branch, 1)  # حساب العمولات
	branch = self.branch
	other_party_profit = self.other_party_profit
	from_party_name = self.from_company
	to_party_name = self.to_company

	try:
		# Validate that the required fields are provided
		if not (debit and credit and profit_account):
			frappe.throw("Debit, Credit, and Profit Account must be specified.")

		# Prepare accounts for the Journal Entry
		accounts = [
			{
				"account": self.debit,  # Specify the debit account
				"branch": branch,
				"party_type": "Customer",
				"party": from_party_name,
				"debit_in_account_currency": debit,
				"credit_in_account_currency": 0,
			},
			{
				"account": self.credit,  # Specify the credit account
				"branch": branch,
				"party_type": "Customer",
				"party": to_party_name,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": credit,
			}
		]
		# Add an entry for out_proft if not 0
		if out_proft != 0:
			accounts.append({
				"account": profit_account,
				"branch": branch,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": out_proft,
			})	
		# Add an entry for other_party_profit if not 0
		if other_party_profit != 0:
			accounts.append({
				"account": profit_account,
				"branch": branch,
				"party_type": "Customer",
				"party": to_party_name,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": other_party_profit,
			})


		# Construct the Journal Entry document
		journal_entry = frappe.get_doc({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"posting_date": frappe.utils.nowdate(),
			"accounts": accounts,
			"mode_of_payment": "Cash",
   			"cheque_no": self.name,
			"cheque_date": frappe.utils.nowdate(),

		})

		# Save and Submit the Journal Entry
		journal_entry.insert(ignore_permissions=True)
		journal_entry.submit()

		frappe.msgprint(f"Journal Entry {journal_entry.name} created successfully.")

		return {
			"status": "success",
			"journal_entry": journal_entry.name
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
		frappe.throw(f"An error occurred while creating the Journal Entry: {str(e)}")
