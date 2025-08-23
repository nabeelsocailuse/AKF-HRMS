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
            options: "Branch",
            default: "Central Office"
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
            options: "Employee",
            get_query(){
                return{
                    filters:{
                        status: 'Active',
                        company: frappe.query_report.get_filter_value("company"),
                        branch: frappe.query_report.get_filter_value("branch"),
                        // department: frappe.query_report.get_filter_value("department"),
                        // designation: frappe.query_report.get_filter_value("designation"),
                        // employment_type: frappe.query_report.get_filter_value("employment_type"),
                        
                    }
                }
            }
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Link",
            options: "Employment Type"
        },
        {
            fieldname: "month",
            label: __("Month"),
            fieldtype: "Select",
            options: [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ],
            default: (function() {
                const currentMonthIndex = new Date().getMonth();
                const months = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ];
                return months[currentMonthIndex];
            })(),
            on_change: function(report) {
                update_dynamic_dates(report);
            }
        },
        {
            fieldname: "year",
            label: __("Year"),
            fieldtype: "Select",
            options: (function() {
                const currentYear = new Date().getFullYear();
                const startYear = currentYear - 4;
                const years = [];
                for (let y = startYear; y <= currentYear; y++) {
                    years.push(y.toString());
                }
                return years.join("\n");
            })(),
            default: new Date().getFullYear().toString(),
            on_change: function(report) {
                update_dynamic_dates(report);
            }
        },
        {
            fieldname: "no_attendance",
            label: __("Is Exempted"),
            fieldtype: "Check",
            reqd: 0,
        },
        {
            fieldname: "from_date",
            label: __("Attendance From Date"),
            fieldtype: "Date",
            reqd: 1,
            hidden: 1
        },
        {
            fieldname: "to_date",
            label: __("Attendance To Date"),
            fieldtype: "Date",
            reqd: 1,
            hidden: 1
        },
        {
            fieldname: "deduction_from_date",
            label: __("Deduction From Date"),
            fieldtype: "Date",
            reqd: 1,
            hidden: 1
        },
        {
            fieldname: "deduction_to_date",
            label: __("Deduction To Date"),
            fieldtype: "Date",
            reqd: 1,
            hidden: 1
        }
    ],

    hidden_columns: [
        "Late Dates",
        "Early Dates",
        "Missing Dates",
        "Leaves Deduction Dates",
        "Absent Dates",
        "Payment Dates"
    ],

    onload: function (report) {
        update_dynamic_dates(report);
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
        // Make Late Entry, Early Exit, and Missing Attendance columns clickable
        if (column.id === "late_entry_count" && data.late_dates) {
            value = `<a href="#" onclick="showDates('(Cur) Late Entry Dates', '${data.late_dates}')">${value}</a>`;
        }
        if (column.id === "cur_app_late_entry_count" && data.cur_app_late_dates) {
            value = `<a href="#" onclick="showDates('(Cur) App Late Entry Dates', '${data.cur_app_late_dates}')">${value}</a>`;
        }
        if (column.id === "pre_late_entry_count" && data.pre_late_dates) {
            value = `<a href="#" onclick="showDates('(Pre) Late Entry Dates', '${data.pre_late_dates}')">${value}</a>`;
        }
        if (column.id === "pre_app_late_entry_count" && data.pre_app_late_dates) {
            value = `<a href="#" onclick="showDates('(Pre) App Late Entry Dates', '${data.pre_app_late_dates}')">${value}</a>`;
        }
        if (column.id === "early_exit_count" && data.early_dates) {
            value = `<a href="#" onclick="showDates('Early Exit Dates', '${data.early_dates}')">${value}</a>`;
        }
        if (column.id === "cur_app_early_exit_count" && data.cur_app_early_dates) {
            value = `<a href="#" onclick="showDates('(Cur) App Early Exit Dates', '${data.cur_app_early_dates}')">${value}</a>`;
        }
        if (column.id === "missing_in_out_count" && data.missing_dates) {
            value = `<a href="#" onclick="showDates('Missing Attendance Dates', '${data.missing_dates}')">${value}</a>`;
        }
        if (column.id === "late_ded" && data.late_ded_dates) {
            value = `<a href="#" onclick="loadDates('Late Entry Deduction Dates', '${data.late_ded_dates}')">${value}</a>`;
        }
        if (column.id === "early_ded" && data.early_ded_dates) {
            value = `<a href="#" onclick="showDates('Early Exit Deduction Dates', '${data.early_ded_dates}')">${value}</a>`;
        }

        if (column.id === "absents" && data.absent_dates) {
            value = `<a href="#" onclick="showDates('Absent Dates', '${data.absent_dates}')">${value}</a>`;
        }
        // if (column.id === "paid_days" && data.paid_dates) {
        //     value = `<a href="#" onclick="showDates('Paid Dates', '${data.paid_dates}')">${value}</a>`;
        // }
        
        return value;
    }
};

function update_dynamic_dates(report) {
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    const selected_month_name = report.get_filter_value("month");
    const selected_year = parseInt(report.get_filter_value("year"));

    if (!selected_month_name || !selected_year) return;

    const selected_month = monthNames.indexOf(selected_month_name);

    const att_from = new Date(selected_year, selected_month - 1, 21); // prev month 21
    const att_to = new Date(selected_year, selected_month, 20);       // current month 20
    const ded_from = new Date(selected_year, selected_month - 2, 21); // prev-prev 21
    const ded_to = new Date(selected_year, selected_month - 1, 20);   // prev 20

    // Formating to yyyy-mm-dd
    function formatDate(d) {
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    report.set_filter_value("from_date", formatDate(att_from));
    report.set_filter_value("to_date", formatDate(att_to));
    report.set_filter_value("deduction_from_date", formatDate(ded_from));
    report.set_filter_value("deduction_to_date", formatDate(ded_to));
}

// Function to show dates in a popup
function showDates(title, dates) {
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

// Function to show dates in a popup
function loadDates(title, dates) {
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