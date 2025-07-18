frappe.ui.keys.add_shortcut(
    {
        description: "internal transfer",
        shortcut: "shift+ctrl+1",
        action: () => {
            frappe.set_route("List", "Internal Transfer")
        }
    }
 
);
frappe.ui.keys.add_shortcut(
{
    description: "transfer between branches",
    shortcut: "shift+ctrl+2",
    action: () => {
        frappe.set_route("List", "transfer between branches")
    }
}

);
frappe.ui.keys.add_shortcut(
{
    description: "company transfer",
    shortcut: "shift+ctrl+3",
    action: () => {
        frappe.set_route("List", "company transfer")
    }
}

)
frappe.ui.toolbar.setup_logo = function() {
    const logo = $(".app-logo-link img");
    const logoLink = $(".app-logo-link");

    if (logo.length) {
        logo.attr("src", "/assets/transfer/images/logo.png");
        logo.css({ height: "32px" }); // optional styling

        logoLink.attr("href", "/app/alalmiatransfer");  // internal route
        logoLink.attr("target", "_self");               // or "_blank" for new tab
    }
};

frappe.after_ajax(() => {
    // If the user lands on /app/home, bounce them to /app/alalmiatransfer
    if (window.location.pathname === "/app/home") {
        window.location.replace("/app/alalmiatransfer");
    }
    if (window.location.pathname === "/app") {
        window.location.replace("/app/alalmiatransfer");
    }
});
