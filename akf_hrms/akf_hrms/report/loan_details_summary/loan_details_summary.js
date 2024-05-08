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
      fieldname: "loan_type",
      label: __("Loan Type"),
      fieldtype: "Link",
      options: "Loan Category",
    },
    {
      fieldname: "repayment_start_date",
      label: __("Repayment Start Date"),
      fieldtype: "Date",
      options: "",
    },
  ],
};
