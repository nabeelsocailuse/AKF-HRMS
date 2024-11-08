
frappe.ready(function() {
    console.log("Mubashir Testingggg");
    if (frappe.user.has_role("Employee") && window.location.pathname === "/app") {
        // Redirect Employee to Self Service if on the default app page
        window.location.href = "/app/self-service";
    }
});

