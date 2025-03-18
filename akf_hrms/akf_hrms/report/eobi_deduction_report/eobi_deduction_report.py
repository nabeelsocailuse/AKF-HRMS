import frappe
from frappe import _

Filters = frappe._dict


def execute(filters: Filters = None) -> tuple:
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns() -> list[dict]:
	columns = [
		{
			"label": _("Posting Date"), 
			"fieldname": "posting_date", 
			"fieldtype": "Date", 
			"width": 140
		},
		{
			"label": _("Employee"),
			"options": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"width": 200,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Gender"),
			"fieldname": "gender",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Employee CNIC"),
			"fieldname": "cnic",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Employee DOB"),
			"fieldname": "employee_dob",
			"fieldtype": "Date",
			"width": 160,
		},
		{
			"label": _("Date of Joining"),
			"fieldname": "date_of_joining",
			"fieldtype": "Date",
			"width": 160,
		},
		{
			"label": _("Employee Address"),
			"fieldname": "employee_address",
			"fieldtype": "Small Text",
			"width": 160,
		},
	]

	columns += [
		{"label": _("EOBI Component"), "fieldname": "eobi", "fieldtype": "Data", "width": 170},
		{
			"label": _("IP Contribution"),
			"fieldname": "ip_contribution",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Employer Contribution"),
			"fieldname": "employer_contribution",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Total Contribution"),
			"fieldname": "total_contribution",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		# {
		# 	"label": _("Gross Pay"),
		# 	"fieldname": "gross_pay",
		# 	"fieldtype": "Currency",
		# 	"options": "currency",
		# 	"width": 140,
		# },
	]

	return columns


def get_data(filters: Filters) -> list[dict]:
	data = []

	deductions = get_eobi_deductions(filters)

	for d in deductions:
		employee = {
			"employee": d.employee,
			"employee_name": d.employee_name,
			"gender": d.custom_gender,
			"cnic": d.custom_cnic,
			"employee_dob": d.custom_employee_dob,
			"date_of_joining": d.custom_date_of_joining,
			"employee_address": d.custom_employee_address,
			"eobi": d.salary_component,
			"ip_contribution": d.amount,
			"employer_contribution": d.custom_eobi_employer_contribution,
			"total_contribution": (d.amount + d.custom_eobi_employer_contribution),
			# "gross_pay": d.gross_pay,
			"posting_date": d.posting_date,
		}

		data.append(employee)

	return data


def get_eobi_deductions(filters: Filters) -> list[dict]:
	SalarySlip = frappe.qb.DocType("Salary Slip")
	SalaryDetail = frappe.qb.DocType("Salary Detail")

	query = (
		frappe.qb.from_(SalarySlip)
		.inner_join(SalaryDetail)
		.on(SalarySlip.name == SalaryDetail.parent)
		.select(
			SalarySlip.employee,
			SalarySlip.employee_name,
			SalarySlip.custom_gender,
			SalarySlip.custom_cnic,
			SalarySlip.custom_employee_dob,
			SalarySlip.custom_date_of_joining,
			SalarySlip.custom_employee_address,
			SalarySlip.posting_date,
			SalaryDetail.salary_component,
			SalaryDetail.amount,
			SalarySlip.custom_eobi_employer_contribution,
			# SalarySlip.gross_pay,
		)
		.where(
			(SalarySlip.docstatus == 1)
			& (SalarySlip.custom_eobi_employee == 1)
			& (SalaryDetail.parentfield == "deductions")
			& (SalaryDetail.parenttype == "Salary Slip")
			& (SalaryDetail.salary_component == "EOBI")
		)
	)

	if filters.get("company"):
		query = query.where(getattr(SalarySlip, "company") == filters.get("company"))

	if filters.get("department"):
		query = query.where(getattr(SalarySlip, "department") == filters.get("department"))
	
	if filters.get("employee"):
		query = query.where(SalarySlip.employee.like(f"{filters.get('employee')}%"))

	if filters.get("fiscal_year"):
		fiscal_year_start, fiscal_year_end = get_fiscal_year_dates(filters.get("fiscal_year"))
		query = query.where(getattr(SalarySlip, "start_date") >= fiscal_year_start)
		query = query.where(getattr(SalarySlip, "end_date") <= fiscal_year_end)

	return query.run(as_dict=True)

def get_fiscal_year_dates(fiscal_year):
    fiscal_year_start = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
    fiscal_year_end = frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
    return fiscal_year_start, fiscal_year_end