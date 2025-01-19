frappe.ui.keys.add_shortcut(

    {
        description: "internal transfer",
        shortcut: "alt+i",
        action: () => {
            frappe.set_route("List", "Internal Transfer")
        }
    }
    ,
    {
        description: "company transfer",
        shortcut: "alt+c",
        action: () => {
            frappe.set_route("List", "Company Transfer")
        }
    },
    {
        description: "branch transfer",
        shortcut: "alt+b",
        action: () => {
            frappe.set_route("List", "transfer between branches")
        }
    }
)a
