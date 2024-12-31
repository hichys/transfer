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
