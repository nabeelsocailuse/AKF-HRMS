// // Developer Mubashir Bashir

frappe.query_reports["Attendance Leave Summary"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },
        {
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Branch"
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department"
        },
        {
            fieldname: "designation",
            label: __("Designation"),
            fieldtype: "Link",
            options: "Designation"
        },
        {
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Link",
            options: "Employment Type"
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: get_default_from_date(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: get_default_to_date(),
            reqd: 1,
        }
    ],

    onload: function (report) {
		hideColumns(report);
		
        if (frappe.user.has_role("Employee")) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    fieldname: ["name", "designation", "department", "branch", "employment_type"],
                    filters: { user_id: frappe.session.user }
                },
                callback: function (response) {
                    if (response && response.message) {
                        const employee_id = response.message.name;
                        const designation = response.message.designation;
                        const department = response.message.department;
                        const branch = response.message.branch;
                        const employment_type = response.message.employment_type;

                        report.set_filter_value("employee", employee_id);
                        if (designation) {
                            report.set_filter_value("designation", designation);
                        }
                        if (department) {
                            report.set_filter_value("department", department);
                        }
                        if (branch) {
                            report.set_filter_value("branch", branch);
                        }
                        if (employment_type) {
                            report.set_filter_value("status", employment_type);
                        }
                    }
                }
            });
        }
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Make Late.Ded, Early.Ded, and Missing.Ded columns clickable
        if (column.id === "late_ded" && data.late_dates) {
            value = `<a href="#" onclick="showDates('Late Entry Dates', '${data.late_dates}')">${value}</a>`;
        }
        if (column.id === "early_ded" && data.early_dates) {
            value = `<a href="#" onclick="showDates('Early Exit Dates', '${data.early_dates}')">${value}</a>`;
        }
        if (column.id === "missing_ded" && data.missing_dates) {
            value = `<a href="#" onclick="showDates('Missing Attendance Dates', '${data.missing_dates}')">${value}</a>`;
        }

        return value;
    }
};

// Function to show dates in a popup
function showDates(title, dates) {
    console.log("click is clicked");

    if (dates) {
        const dateArray = dates.split(',');

        const formattedDates = dateArray.map(date => {
            const [year, month, day] = date.split('-');
            return `${day}-${month}-${year}`; 
        });

        const formattedMessage = formattedDates.join('<br>');

        frappe.msgprint({
            title: title,
            message: formattedMessage
        });
    } else {
        frappe.msgprint({
            title: title,
            message: "No dates found."
        });
    }
}

function hideColumns(report) {
	console.log('hide columns');
	
    const columnsToHide = ["late_dates", "early_dates", "missing_dates"];

    // Iterate through columns and hide the specified ones
    report.columns.forEach(column => {
        if (columnsToHide.includes(column.id)) {
            column.hidden = true;
        }
    });

    // Refresh the report to apply changes
    report.refresh();
}

// Function to get default from date
function get_default_from_date() {
    const today = new Date();
    const day = today.getDate();
    const month = today.getMonth();
    const year = today.getFullYear();

    let from_date;

    if (day > 20) {
        from_date = new Date(year, month, 22).toISOString().split("T")[0];
    } else {
        from_date = new Date(year, month - 1, 22).toISOString().split("T")[0];
    }

    console.log("Calculated from_date:", from_date);
    return from_date;
}

// Function to get default to date
function get_default_to_date() {
    const today = new Date();
    const day = today.getDate();
    const month = today.getMonth();
    const year = today.getFullYear();

    let to_date;

    if (day > 20) {
        to_date = new Date(year, month + 1, 21).toISOString().split("T")[0];
    } else {
        to_date = new Date(year, month, 21).toISOString().split("T")[0];
    }

    console.log("Calculated to_date:", to_date);
    return to_date;
}
