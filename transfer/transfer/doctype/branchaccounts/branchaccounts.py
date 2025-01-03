# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BranchAccounts(Document):
	pass


###
# generate_accounts()
# get branch and generate accounts for it
#1001 -> meaing main account --> goes to accounts index 0
#2001 -> meaning profit account -> goes to accounts index 1
#3001 -> meaning temp account -> goes to accounts index 2
#get list of avaliable doctype(branch) check  first if its has generated before
#get the 3 accounts for the branch its use filter to get the 3 accounts
#check if its valid (3 accounts) skip if not //show_msg alert
#let branch_code be the main account name but take the number only
#save the doc and submit it###
@frappe.whitelist()
def generate_accounts():
	# get all branches
	branches = frappe.get_all('Branch', fields=['branch'])
	
	# loop through branches
	for branch in branches:
		# check if branch accounts already generated
		if frappe.db.exists("BranchAccounts", {"branch_name": branch.branch}):
			
			frappe.msgprint(f"BranchAccounts already generated for {branch.branch}")
			continue
		
		
		# get branch accounts
		# fillter with account_name contains branch.branch
		
		branch_accounts = frappe.get_all("Account", filters={"account_name": ["like", f"%{branch.branch}%"]}, fields=["name", "account_number"])
		frappe.msgprint(f"{branch_accounts}")
		# check if branch accounts are valid
		
		
		#configm branch accounts all contains the same same branch name and series number #1001,2001,3001
		#branch_accounts[0] is the main account
		#branch_accounts[1] is the profit account
		#branch_accounts[2] is the temp account
		#check if the branch accounts are valid
		#skip if not
		#show_msg alert
	 
		if len(branch_accounts) != 3:
			frappe.msgprint(f"Skipping branch '{branch.branch}' - incomplete account data.")
			continue
		
		# create BranchAccounts document
		branch_accounts_doc = frappe.new_doc("BranchAccounts")
		branch_accounts_doc.branch_name = branch.branch
		branch_accounts_doc.branch_code = branch_accounts[0].account_number
		#append bracnh accounts to the child table
		#save the doc
		#commit the transaction
		branch_accounts_doc.append("accounts", {"account": branch_accounts[0].name, "desc": "Main Account"})
		branch_accounts_doc.append("accounts", {"account": branch_accounts[1].name, "desc": "Profit Account"})
		branch_accounts_doc.append("accounts", {"account": branch_accounts[2].name, "desc": "Temporary Account"})
		branch_accounts_doc.insert()
		#save and submit the doc
		branch_accounts_doc.submit()

		frappe.db.commit()
		frappe.msgprint(f"BranchAccounts created for branch: {branch.branch}")