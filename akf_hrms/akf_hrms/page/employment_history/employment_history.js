frappe.pages['employment-history'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employment History Report',
        single_column: true
    });

    let filters = {};

    filters.add = function(page) {
        let company = page.add_field({
            "label": "Company Name",
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1,
            change() {
                filters.company = company.get_value();
                set_employee_query();
            }
        });

        let employee = page.add_field({
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            change() {
                filters.employee = employee.get_value();
                if (filters.company) {
                    api.loadRealTimeInformation(page, filters);
                } else {
                    frappe.msgprint("Please select a company first.");
                }
            }
        });

        let btnPrint = page.add_field({
            "label": "Print",
            "fieldname": "print",
            "fieldtype": "Button",
            "options": "",
            click() {
                printContentFunc();
            }
        });

        let btnRefresh = page.add_field({
            "label": "Refresh",
            "fieldname": "refresh",
            "fieldtype": "Button",
            "options": "",
            click() {
                refreshEmployeeInformation();
            }
        });

        $(btnPrint.$wrapper).hide();
        $(btnRefresh.$wrapper).hide();

        function set_employee_query() {
            employee.get_query = function() {
                if (filters.company) {
                    return {
                        filters: {
                            'company': filters.company
                        }
                    };
                } else {
                    return {
                        filters: {
                            'company': ""
                        }
                    };
                }
            };
        }

        set_employee_query();
    };

    const api = {
        loadRealTimeInformation: function(page, filters) {
            frappe.call({
                method: 'akf_hrms.akf_hrms.page.employment_history.employment_history.get_information',
                args: {
                    filters: JSON.stringify(filters)
                },
                freeze: true,
                freeze_message: "Fetching employee information...",
                callback: function(r) {
                    console.log(r.message);
                    design.loadDesign(page, r.message);
                    // Show Print and Refresh buttons once the employee record is being shown.
                    if (filters.employee) {
                        page.fields_dict.print.$wrapper.show();
                        page.fields_dict.refresh.$wrapper.show();
                    } else {
                        page.fields_dict.print.$wrapper.hide();
                        page.fields_dict.refresh.$wrapper.hide();
                    }
                }
            });
        }
    };

    const design = {
        loadDesign: function(page, info) {
            $(".employee").remove();
            const content = frappe.render_template("employment_history", info);
            $(content).appendTo(page.main);
        }
    };

    filters.add(page);

    function printContentFunc() {
        let content = $(".container-fluid.employee").html();
        frappe.call({
            method: "akf_hrms.akf_hrms.page.employment_history.employment_history.set_print_content",
            args: {
                content: content
            },
            callback: function(r) {
                if (r.message && r.message === "Content successfully set for printing") {
                    window.print();
                } else {
                    frappe.msgprint("Error occurred while setting content for printing.");
                }
            }
        });
    }

    function refreshEmployeeInformation() {
        if (filters.company && filters.employee) {
            api.loadRealTimeInformation(page, filters);
        } else {
            frappe.msgprint("Please select a company and an employee first.");
        }
    }
};
