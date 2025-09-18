# Copyright (c) 2025, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from transfer.transfer.api import get_customer_account,get_account_balance,get_company_main_account,create_journal_entry_preview, delete_draft_doc, validate_linked_journal_entries,create_journal_entry as cr_j,get_main_account,get_profit_account,get_currency_remaining_qty,get_account_for_branch,get_temp_account, is_posting_day_today
from frappe.utils import getdate, nowdate 
from erpnext.accounts.utils import get_balance_on
from .it_api import *
from frappe import _
class InternalTransfer(Document):
	def before_cancel(self):
		validate_linked_journal_entries(self.name)
		self.status = "ملغية"

	def on_update_after_submit(self):
		if self.delivery_date and self.posting_date:
			if getdate(self.delivery_date) < getdate(self.posting_date):
				frappe.throw(_("تاريخ التسليم يجيب ان يكون اكبر من تاريخ الحوالة"))

	def validate(self):
		if self.delivery_date and self.posting_date:
			if getdate(self.delivery_date) < getdate(self.posting_date):
				frappe.throw(_("تاريخ التسليم يجيب ان يكون اكبر من تاريخ الحوالة"))



def getDoc(docname):
	return frappe.get_doc("Internal Transfer",docname)
	 

@frappe.whitelist()
def handel_journal_entries_creation(docname):
	doc = frappe.get_doc("Internal Transfer",docname)

	#بدون تعليق الحوالة
	if doc.select_internal == "من فرع الي شركة":
		# frappe.msgprint("handel journal enteris من فرع الي شركة")
		create_journal_entry(doc,temp=False)
	#الحوالة تعلق لين تستلم
	if doc.select_internal == "من شركة الي فرع" :
		# frappe.msgprint("#######")
		create_journal_entry(doc,temp=True)

@frappe.whitelist()
def create_journal_entry(self,temp=False):
	
	profit = self.our_profit
	profit_account = get_profit_account(self.branch)

	debit = self.debit
	credit = self.credit
	branch = self.branch

	if (self.from_type and self.to_type):
		if(self.from_type == "Branch"):
			debit = get_main_account(self.branch)
			credit = get_customer_account(self.to_type)
		else:
			credit = get_temp_account(self.branch)
			debit= get_customer_account(self.to_type)
		frappe.msgprint(f"debit {debit}, credit{credit}")
	else:
		frappe.throw("الرجاء اختيار نوع التحويلة اولا والمرسل والمستقبل")


	our_profit = self.our_profit
	other_party_profit = self.other_party_profit
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

		# from company to branch 25  -  out_profit = 2 , other 5
		# branch debit   27
		# company credit 25 + out_profit(2)

		if(self.from_type == "Customer"):
			frappe.msgprint("من شركة الي فرع")
			from_type = "Customer"
			from_party_type = from_party_name
			to_type = ""
			to_party_type = ""
			debit_in_account_currency =  self.amount  +  other_party_profit 
			credit_in_account_currency = self.amount  
		else :
			if(self.to_type == "Customer" and self.from_type != "Customer"):
				to_type = "Customer"
				to_party_type = to_party_name
				debit_in_account_currency =  self.amount  + other_party_profit +our_profit
				credit_in_account_currency = self.amount   + other_party_profit  
				from_type = ""
				from_party_type = ""
	 
			
			
		# Prepare accounts for the Journal Entry
		accounts = [
			{
				"account": debit,  # Specify the debit account
				"branch": branch,
				"party_type": from_type,
				"party": from_party_type,
				"debit_in_account_currency": debit_in_account_currency,
				"credit_in_account_currency": 0,
			},
			{
				"account": credit,  # Specify the credit account
				"branch": branch,
				"party_type": to_type,
				"party": to_party_type,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": credit_in_account_currency,
			}
		]
		# Add an entry for out_proft if not 0
		if(self.from_type == "Customer"):
			if other_party_profit != 0:
				accounts.append(
					{
					"account": profit_account,
					"branch": branch,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": other_party_profit,
					}
				)	
		else:
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
			"user_remark" : self.whatsapp_desc

		})

		# Save and Submit the Journal Entry
		journal_entry.insert(ignore_permissions=True)
		journal_entry.submit()
		#self.journal_entry = journal_entry.name
		
  
		if journal_entry.docstatus != 1 :
			frappe.throw("خطا كود 1025 الرجاء مراجعة الادمن")
   
		self.status = "غير مستلمة"
		self.save()
  
		# frappe.msgprint(f"Journal Entry {journal_entry.name} created successfully.")
		frappe.msgprint(f"تم انشاء الحوالة بنجاح")
		return {
			"status": "success",
			"journal_entry": journal_entry.name
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
		frappe.throw(f"An error(888) occurred while creating the Journal Entry: {str(e)}")
 

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
				"reversal_of": journal_entry.name,
				"user_remark":journal_entry.user_remark
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

@frappe.whitelist()
def handel_cancellation(docname):
	# 2 options cancel the journal entrey -> if he cancel during the day
	# or revese it => if he cancel in another day
	doc =frappe.get_doc("Internal Transfer",docname)
	if is_posting_day_today(doc.posting_date) :
		if(it_cancel_journal_entries(doc)):
			doc.cancel()
			frappe.msgprint("تم إلغاء الحوالة بنجاح")
	else:
		it_reverse_journal_entries(doc)
@frappe.whitelist()
def transfer_completed(docname):
	try:
		# Fetch the document
		doc = frappe.get_doc("Internal Transfer", docname)
		
		# Get the target account
		from_acc = get_temp_account(doc.branch)
		to_acc = get_main_account(doc.branch)
		
		# Validate if transfer is from the main account and to the correct branch
		if doc.check_tslmfrommain:
			if doc.to_company== frappe.get_cached_doc("Transfer Setting").main_branch:
				from_acc = get_company_main_account()
				to_acc = get_temp_account(doc.branch)
			# Validate if the from_account has sufficient balance
				from_account_balance = get_balance_on(get_company_main_account(),date=nowdate())
				if from_account_balance < doc.amount:
					frappe.throw(f"الرصيد غير كافي في الحساب. الرصيد الحالي: {from_account_balance}, المبلغ المطلوب: {doc.amount}")
				
			else:
				frappe.throw("التسليم من الخزنة الرئسية غير متوفر لهذا الفرع")
		
		# Check if the transfer is from a customer
		if doc.from_type == "Customer":
			# Create journal entry
			cr_j(
				from_account=from_acc,
				to_account=to_acc,
				branch=doc.branch,
				amount=doc.amount,
				cheque_no=docname,
				posting_date=nowdate(),
				remarks=doc.whatsapp_desc
			)
		 
		# Update the document's status
		doc.status = "مستلمة"
		doc.save()
		frappe.db.commit()
	
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in transfer_completed")


