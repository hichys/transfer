import frappe
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


import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_account_for_branch(branch_name, account_index=0):
    # Convert account_index to integer (in case it's passed as a string)
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

    return None


# create journal entry from data in Doc
def make_journal_entry(self, from_branch, to_branch,from_commision,to_commision, commission_amount, transaction_type):
    try:
        customer = self.customer
        if transaction_type == "transfer":
            customer = self.to
        total_amount = flt(self.amount)
        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.posting_date = today()
        journal_entry.user_remark = self.name #desc
        #from branch
        if self.amount != 0 and from_branch and to_branch:
            journal_entry.append("accounts",
                                 {
                                     "account": from_branch,
                                     "credit_in_account_currency": 0,
                                     "debit_in_account_currency": total_amount,
                                 }
                                 )
            #to branch
            journal_entry.append("accounts",
                                 {
                                     "account": to_branch,
                                     "credit_in_account_currency": total_amount,
                                     "debit_in_account_currency": 0
                                 }
                                 )
            if (commission_amount== 0):
              journal_entry.save()
              journal_entry.docstatus  = 1
       
      
            if (commission_amount):
                if (transaction_type == "لم تسلم"): # status
                    journal_entry.append("accounts",
                                         {
                                             "account": from_commision,
                                             "credit_in_account_currency": flt(commission_amount/2),
                                             "debit_in_account_currency": 0,
                                         }
                                         )
                    journal_entry.append("accounts",
                                         {
                                             "account": to_commision,
                                             "credit_in_account_currency": flt(commission_amount/2),
                                             "debit_in_account_currency": 0,
                                         }
                                         )
                elif (transaction_type == "تم1 التسليم"):
                    journal_entry.append("accounts",
                                         {
                                             "account": debit,
                                             "credit_in_account_currency": 0,
                                             "debit_in_account_currency": flt(commission_amount/2),
                                         }
                                         )
                elif (transaction_type == "راجعه1 او ملغية" and commission_amount > 0 ):
                    journal_entry.append("accounts",
                                         {
                                             "account": debit, "party_type": "Customer",
                                             "party": self.customer,
                                             "exchange_rate": self.exchange_rate,
                                             "credit_in_account_currency": 0,
                                             "debit_in_account_currency": flt(commission_amount),
                                         }
                                         )
                    
                    
                    journal_entry.append("accounts",
                                        {
                                            "account": commission_account,
                                            "exchange_rate": self.exchange_rate,
                                            "credit_in_account_currency": flt(commission_amount),
                                            "debit_in_account_currency": 0,
                                        }
                                        )
                    journal_entry.save()
                    journal_entry.docstatus  = 1
       
            
            journal_entry.save()
            journal_entry.docstatus  = 1
       
            self.db_set("journal_entry", journal_entry.name)
            self.db_set("created_by", frappe.session.user)
            
           # self.save()
           # frappe.db.commit()
    except Exception as e:
        print(e)
        traceback = frappe.get_traceback()
        frappe.log_error(
            title=_("Error while creating journal entry for {}".format(self.name)),
            message=traceback,
        ) 