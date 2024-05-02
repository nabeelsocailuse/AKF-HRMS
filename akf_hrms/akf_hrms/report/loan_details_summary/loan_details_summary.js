// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Loan Details Summary"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
    },
    {
      fieldname: "applicant",
      label: __("Employee ID"),
      fieldtype: "Link",
      options: "Employee",
    },
    {
      fieldname: "branch",
      label: __("Branch"),
      fieldtype: "Link",
      options: "Branch",
    },
    {
      fieldname: "repayment_status",
      label: __("Repayment Status"),
      fieldtype: "Select",
      options: ["", "Paid", "unpaid"],
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      options: "",
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      options: "",
    },
    {
      fieldname: "loan_type",
      label: __("Loan Type"),
      fieldtype: "Link",
      options: "Loan Category",
    },
  ],
};
