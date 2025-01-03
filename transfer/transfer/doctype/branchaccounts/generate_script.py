import frappe
import os
import csv

def create_branch_accounts_from_csv():
    # CSV configuration (input file path)
    input_csv_file = "accounts.csv"
    
    # Check if the file exists
    if not os.path.exists(input_csv_file):
        print(f"Error: The file '{input_csv_file}' was not found.")
        return

    # Read the CSV file
    accounts_data = []
    try:
        with open(input_csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            accounts_data = [row for row in reader]
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Create BranchAccounts for each branch
    branches_processed = set()

    for row in accounts_data:
        account_name_parts = row["Account Name"].split()
        
        if len(account_name_parts) > 1:  # Ensure there are at least two parts
            branch_name = account_name_parts[1]  # Extract branch name
            account_type = account_name_parts[0]  # Extract account type
            account_name = row["Account Name"]
            account_number = row["Account Number"]

            # Skip if this branch was already processed
            if branch_name in branches_processed:
                continue

            # Filter accounts for the current branch
            branch_accounts = [
                acc for acc in accounts_data if acc["Account Name"].split()[1] == branch_name
            ]

            # Ensure all 3 accounts (main, profit, temp) are present
            if len(branch_accounts) < 3:
                print(f"Skipping branch '{branch_name}' - incomplete account data.")
                continue

            # Create BranchAccounts document
            branch_accounts_doc = frappe.new_doc("BranchAccounts")
            branch_accounts_doc.branch_name = branch_name
            branch_accounts_doc.branch_code = account_number  # You can customize this field

            # Map accounts into the child table
            for acc in branch_accounts:
                acc_type = acc["Account Name"].split()[0]  # Main/Profit/Temp
                desc = "Main Account" if acc_type == "خزنة" else "Profit Account" if acc_type == "عمولات" else "Temporary Account"
                branch_accounts_doc.append("accounts", {"account": acc["Account Name"], "desc": desc})

            # Save the document
            try:
                branch_accounts_doc.insert()
                frappe.db.commit()
                print(f"BranchAccounts created for branch: {branch_name}")
                branches_processed.add(branch_name)
            except Exception as e:
                print(f"Error creating BranchAccounts for branch '{branch_name}': {e}")
        else:
            print(f"Account Name '{row['Account Name']}' does not have enough parts to extract branch information.")

# Call the function
create_branch_accounts_from_csv()
