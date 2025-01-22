
frappe.ui.form.on("Company", {
    refresh: function(frm) {
        frm.set_query("custom_default_donation_in_kind_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });
        frm.set_query("custom_default_project_fund_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });
        frm.set_query("custom_default_unrestricted_fund_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });
        frm.set_query("custom_default_fund", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });
        frm.set_query("custom_default_inventory_fund_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });
        frm.set_query("custom_default_regional_inventory_fund_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });
        frm.set_query("custom_default_designated_asset_fund_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Equity'
                }
            };
        });

        frm.set_query("custom_default_retention_payable_account", function() {
            return {
                filters: {
                    "company": frm.doc.name,
                    "root_type": 'Liability',
                    "account_type": 'Payable',
                }
            };
        });
    },
    
});
