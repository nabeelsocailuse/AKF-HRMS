# Mubashir Bashir, 14-05-2025

import frappe
from frappe import _
from frappe.utils import flt
import json

import erpnext



salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")

# print("This is my salary  detail",salary_detail)

salary_component = frappe.qb.DocType("Salary Component")


def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)

	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips, filters)
	columns = get_columns(earning_types, ded_types)

	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings", filters)
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions", filters)		
	doj_map = get_employee_doj_map()

	data = []
	department_totals = {}
	
	# First pass - collect all records and calculate department totals
	for ss in salary_slips:
		row = {
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"data_of_joining": doj_map.get(ss.employee),
			"branch": ss.branch,
			"department": ss.department,
			"designation": ss.designation,
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": ss.leave_without_pay,
			"payment_days": ss.payment_days,
			"gross_salary": frappe.utils.fmt_money(ss.custom_gross_salary, currency=currency or company_currency),
			"currency": currency or company_currency,
			"total_loan_repayment": frappe.utils.fmt_money(ss.total_loan_repayment, currency=currency or company_currency),
		}

		update_column_width(ss, columns)

		for e in earning_types:
			amount = ss_earning_map.get(ss.name, {}).get(e) or 0
			row.update({frappe.scrub(e): frappe.utils.fmt_money(amount, currency=currency or company_currency)})
			if ss.department:
				department_totals.setdefault(ss.department, {}).setdefault(frappe.scrub(e), 0)
				department_totals[ss.department][frappe.scrub(e)] += amount

		for d in ded_types:
			amount = ss_ded_map.get(ss.name, {}).get(d) or 0
			row.update({frappe.scrub(d): frappe.utils.fmt_money(amount, currency=currency or company_currency)})
			if ss.department:
				department_totals.setdefault(ss.department, {}).setdefault(frappe.scrub(d), 0)
				department_totals[ss.department][frappe.scrub(d)] += amount

		if currency == company_currency:
			gross_pay = flt(ss.gross_pay) * flt(ss.exchange_rate)
			total_deduction = flt(ss.total_deduction) * flt(ss.exchange_rate)
			net_pay = flt(ss.net_pay) * flt(ss.exchange_rate)
		else:
			gross_pay = ss.gross_pay
			total_deduction = ss.total_deduction
			net_pay = ss.net_pay

		row.update({
			"gross_pay": frappe.utils.fmt_money(gross_pay, currency=currency or company_currency),
			"total_deduction": frappe.utils.fmt_money(total_deduction, currency=currency or company_currency),
			"net_pay": frappe.utils.fmt_money(net_pay, currency=currency or company_currency)
		})

		# Update department totals
		if ss.department:
			department_totals.setdefault(ss.department, {}).setdefault("gross_pay", 0)
			department_totals.setdefault(ss.department, {}).setdefault("total_deduction", 0)
			department_totals.setdefault(ss.department, {}).setdefault("net_pay", 0)
			department_totals.setdefault(ss.department, {}).setdefault("leave_without_pay", 0)
			department_totals.setdefault(ss.department, {}).setdefault("payment_days", 0)
			department_totals.setdefault(ss.department, {}).setdefault("gross_salary", 0)
			department_totals.setdefault(ss.department, {}).setdefault("total_loan_repayment", 0)
			
			department_totals[ss.department]["gross_pay"] += gross_pay
			department_totals[ss.department]["total_deduction"] += total_deduction
			department_totals[ss.department]["net_pay"] += net_pay
			department_totals[ss.department]["leave_without_pay"] += flt(ss.leave_without_pay or 0)
			department_totals[ss.department]["payment_days"] += flt(ss.payment_days or 0)
			department_totals[ss.department]["gross_salary"] += flt(ss.custom_gross_salary or 0)
			department_totals[ss.department]["total_loan_repayment"] += flt(ss.total_loan_repayment or 0)

		data.append(row)

	# Sort data by department
	data.sort(key=lambda x: (x.get("department") or ""))

	# Second pass - add department total rows
	final_data = []
	current_department = None
	grand_totals = {}

	for row in data:
		if current_department != row.get("department"):
			if current_department and current_department in department_totals:
				# Add total row for previous department
				total_row = {
					# "employee_name": f"<b>{current_department}</b>",
					# "department": current_department,
					"employee_name": "",
					"department": "",
					"is_total": 1
				}
				# Add values without bold tags
				for key, value in department_totals[current_department].items():
					if key in ["gross_pay", "total_deduction", "net_pay", "gross_salary", "total_loan_repayment"] or key in [frappe.scrub(e) for e in earning_types] or key in [frappe.scrub(d) for d in ded_types]:
						total_row[key] = f"<b>{frappe.utils.fmt_money(value, currency=currency or company_currency)}</b>"
					else:
						total_row[key] = f"<b>{value}</b>"
					# Update grand totals
					grand_totals.setdefault(key, 0)
					grand_totals[key] += value
				final_data.append(total_row)
				# Add empty row after department total
				empty_row = {
					"employee_name": "",
					"department": "",
					"gross_pay": "",
					"total_deduction": "",
					"net_pay": "",
					"leave_without_pay": "",
					"payment_days": "",
					"gross_salary": "",
					"total_loan_repayment": ""
				}
				# Add None for all earning and deduction fields
				for e in earning_types:
					empty_row[frappe.scrub(e)] = ""
				for d in ded_types:
					empty_row[frappe.scrub(d)] = ""
				final_data.append(empty_row)
			
			current_department = row.get("department")
			
			# Add empty row with department name before the first row of each department
			empty_row = {
				"employee_name": f"<b>{current_department}</b>",
				"department": current_department,
				"gross_pay": "",
				"total_deduction": "",
				"net_pay": "",
				"leave_without_pay": "",
				"payment_days": "",
				"gross_salary": "",
				"total_loan_repayment": ""
			}
			# Add None for all earning and deduction fields
			for e in earning_types:
				empty_row[frappe.scrub(e)] = ""
			for d in ded_types:
				empty_row[frappe.scrub(d)] = ""
			final_data.append(empty_row)
		
		final_data.append(row)

	# Add total row for last department
	if current_department and current_department in department_totals:
		total_row = {
			# "employee_name": f"<b>{current_department}</b>",
			"employee_name": "",
			"department": '',
			"is_total": 1
		}
		# Add values without bold tags
		for key, value in department_totals[current_department].items():
			if key in ["gross_pay", "total_deduction", "net_pay", "gross_salary", "total_loan_repayment"] or key in [frappe.scrub(e) for e in earning_types] or key in [frappe.scrub(d) for d in ded_types]:
				total_row[key] = f"<b>{frappe.utils.fmt_money(value, currency=currency or company_currency)}</b>"
			else:
				total_row[key] = f"<b>{value}</b>"
			# Update grand totals
			grand_totals.setdefault(key, 0)
			grand_totals[key] += value
		final_data.append(total_row)
		# Add empty row after last department total
		empty_row = {
			"employee_name": "",
			"department": "",
			"gross_pay": "",
			"total_deduction": "",
			"net_pay": "",
			"leave_without_pay": "",
			"payment_days": "",
			"gross_salary": "",
			"total_loan_repayment": ""
		}
		# Add None for all earning and deduction fields
		for e in earning_types:
			empty_row[frappe.scrub(e)] = ""
		for d in ded_types:
			empty_row[frappe.scrub(d)] = ""
		final_data.append(empty_row)

	# Add grand total row at the end
	if grand_totals:
		grand_total_row = {
			"employee_name": "<b>Grand Total</b>",
			"is_total": 1
		}
		for key, value in grand_totals.items():
			if key in ["gross_pay", "total_deduction", "net_pay", "gross_salary", "total_loan_repayment"] or key in [frappe.scrub(e) for e in earning_types] or key in [frappe.scrub(d) for d in ded_types]:
				grand_total_row[key] = f"<b>{frappe.utils.fmt_money(value, currency=currency or company_currency)}</b>"
			else:
				grand_total_row[key] = f"<b>{value}</b>"
		final_data.append(grand_total_row)

	return columns, final_data

def get_earning_and_deduction_types(salary_slips, filters):
	salary_component_and_type = {_("Earning"): [], _("Deduction"): []}
	for salary_component in get_salary_components(salary_slips):
		if(filters.get("non_taxable_component")): # Nabeel Saleem, 07-03-2025
			if(salary_component.custom_non_taxable_component):
				pass
			else:
				component_type = get_salary_component_type(salary_component.salary_component)
				salary_component_and_type[_(component_type)].append(salary_component.salary_component)
		else:
			component_type = get_salary_component_type(salary_component.salary_component)
			salary_component_and_type[_(component_type)].append(salary_component.salary_component)

	return sorted(salary_component_and_type[_("Earning")]), sorted(
		salary_component_and_type[_("Deduction")]
	)

def getting_salary_components(salary_slips):
	frappe.throw("Hellow how are you")
	
	query = (
		frappe.qb.from_(salary_detail)
		
		.where(
			(salary_detail.amount != 0)
			& (salary_detail.parent.isin([e.name for e in salary_slips]))
			# &(salary_detail.custom_non_taxable_component == 1)  
			& (salary_detail.parentfield == "earnings")
		)
		.select(salary_detail.salary_component)
		.distinct()
	)

	return [row[0] for row in query.run(as_dict=False)]  

def update_column_width(ss, columns):
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		columns[9].update({"width": 120})


def get_columns(earning_types, ded_types):
	columns = [
		{
			"label": _("Salary Slip ID"),
			"fieldname": "salary_slip_id",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Date of Joining"),
			"fieldname": "data_of_joining",
			"fieldtype": "Date",
			"width": 80,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": -1,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": -1,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Leave Without Pay"),
			"fieldname": "leave_without_pay",
			"fieldtype": "Data",
			"width": 50
		},
		{
			"label": _("Payment Days"),
			"fieldname": "payment_days",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Gross Salary"),
			"fieldname": "gross_salary",
			"fieldtype": "Data",
			"width": 120
		},
	]

	for earning in earning_types:
		columns.append(
			{
				"label": earning,
				"fieldname": frappe.scrub(earning),
				"fieldtype": "Data",
				"width": 120
			}
		)

	columns.append(
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Data",
			"width": 120
		}
	)

	for deduction in ded_types:
		columns.append(
			{
				"label": deduction,
				"fieldname": frappe.scrub(deduction),
				"fieldtype": "Data",
				"width": 120
			}
		)

	columns.extend(
		[
			{
				"label": _("Loan Repayment"),
				"fieldname": "total_loan_repayment",
				"fieldtype": "Data",
				"width": 120
			},
			{
				"label": _("Total Deduction"),
				"fieldname": "total_deduction",
				"fieldtype": "Data",
				"width": 120
			},
			{
				"label": _("Net Pay"),
				"fieldname": "net_pay",
				"fieldtype": "Data",
				"width": 120
			},
			{
				"label": _("Currency"),
				"fieldtype": "Data",
				"fieldname": "currency",
				"options": "Currency",
				"hidden": 1,
			},
			{
				"label": _("Is Total"),
				"fieldname": "is_total",
				"fieldtype": "Check",
				"hidden": 1,
			},
		]
	)

	return columns


def get_salary_components(salary_slips):
	return (
		frappe.qb.from_(salary_detail)
		.where((salary_detail.amount != 0) & (salary_detail.parent.isin([d.name for d in salary_slips])))
		.select(salary_detail.salary_component, salary_detail.custom_non_taxable_component)
		.distinct()
	).run(as_dict=True)	
	# ).run(pluck=True)



def get_salary_component_type(salary_component):
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)


def get_salary_slips(filters, company_currency):
	from frappe.query_builder.custom import ConstantColumn

	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	query = frappe.qb.from_(salary_slip).select(salary_slip.star)

	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.start_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.end_date <= filters.get("to_date"))

  
	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	if filters.get("branch"):
		query = query.where(salary_slip.branch == filters.get("branch"))
	
	if filters.get("department"):
		query = query.where(salary_slip.department == filters.get("department"))
	
	if filters.get("designation"):
		query = query.where(salary_slip.designation == filters.get("designation"))
	
	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))
	
	# if filters.get("non_taxable_component"): 
	# 	query = query.where(salary_detail.custom_non_taxable_component == 1) 
			   
		
	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))
  
	
	salary_slips = query.run(as_dict=1)
	
	return salary_slips or []


def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)

def get_salary_slip_details(salary_slips, currency, company_currency, component_type, filters):
	salary_slips = [ss.name for ss in salary_slips]
 
	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
			salary_detail.custom_non_taxable_component
		)
	).run(as_dict=1)

	ss_map = {}
	non_taxable_component = filters.get("non_taxable_component")
	for d in result:
		if(d.custom_non_taxable_component ==non_taxable_component): # Nabeel Saleem, 07-03-2025
			continue
		else:
			ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
			if currency == company_currency:
				ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
					d.exchange_rate if d.exchange_rate else 1
				)
			else:
				ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map
