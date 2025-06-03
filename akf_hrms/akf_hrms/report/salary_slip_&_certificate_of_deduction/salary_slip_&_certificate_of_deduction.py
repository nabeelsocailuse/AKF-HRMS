	# Mubashir Bashir 21-05-2025

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
	columns, data = [], []
	months = ["July", "August", "September", "October", "November", "December", 
			 "January", "February", "March", "April", "May", "June"]
	columnss = get_columns(filters, months)
	columns = columnss[0]
	data = get_employees(filters, columnss[1], months)
	return columns, data

def get_columns(filters, months):
	columns = []
	columns.append({
		"label": _("Components"),
		"fieldtype": "Data",
		"fieldname": "components",
		"width": 150
	})
	
	for key, value in enumerate(months):
		year = filters.fiscal_year.split("-")[0] if int(key) < 6 else filters.fiscal_year.split("-")[1]
		columns.append({
			"label": _("") + str(value) + "-" + str(year),
			"fieldtype": "Data",
			"fieldname": "mm-" + str(key),
			"width": 120
		})
	
	columns.append({
		"label": _("Total"),
		"fieldtype": "Data",
		"fieldname": "total",
		"width": 150
	})
	return columns, len(columns)

def get_employees(filters, length, months):
	detail = []
	
	if "Accounts User" not in frappe.get_roles(frappe.session.user):
		check_emp_per = frappe.db.sql("""select name from `tabEmployee` where user_id=%s """, (frappe.session.user))
		if check_emp_per:
			if check_emp_per[0][0] != str(filters.employee):
				frappe.throw("You can only view your own salary information")
		else:
			frappe.throw("Record Not Found")

	components_query = """
		SELECT DISTINCT salary_component, parentfield
		FROM (
			SELECT salary_component, parentfield 
			FROM `tabSalary Detail` sd
			INNER JOIN `tabSalary Slip` ss ON sd.parent = ss.name
			WHERE ss.employee = %s 
			AND ss.company = %s 
			AND ss.docstatus = 1
			AND (
				(sd.parentfield = 'earnings' AND sd.is_tax_applicable = 1)
				OR sd.parentfield = 'deductions'
			)
			AND (
				(MONTH(ss.start_date) >= 7 AND YEAR(ss.start_date) = %s)
				OR 
				(MONTH(ss.start_date) < 7 AND YEAR(ss.start_date) = %s)
			)
		) as components
		ORDER BY parentfield, salary_component
	"""
	
	components = frappe.db.sql(components_query, (
		filters.employee, 
		filters.company,
		filters.fiscal_year.split('-')[0],  # For July-Dec
		filters.fiscal_year.split('-')[1]   # For Jan-Jun
	))

	earnings_components = [comp[0] for comp in components if comp[1] == 'earnings']
	deduction_components = [comp[0] for comp in components if comp[1] == 'deductions']

	# Create the final list with desired order
	earnings_and_deductions = (
		earnings_components + 
		["<b>Total Earning</b>"] + 
		deduction_components + 
		["<b>Total Deduction</b>"] + 
		["<b>NET SALARY</b>"]
	)

	row_no = 1
	sum_of_payments = 0.0
	
	for component in earnings_and_deductions:
		total = [""] * length
		total[0] = component

		for i, month in enumerate(months, 1):
			salary_slip_query = """
				SELECT name 
				FROM `tabSalary Slip` 
				WHERE employee = %s 
				AND company = %s 
				AND MONTH(start_date) = %s 
				AND docstatus = 1 
				AND (
					(MONTH(start_date) >= 7 AND YEAR(start_date) = %s)
					OR 
					(MONTH(start_date) < 7 AND YEAR(start_date) = %s)
				)
			"""
			
			month_num = datetime.strptime(month, '%B').month
			year = filters.fiscal_year.split('-')[0] if month in ['July', 'August', 'September', 'October', 'November', 'December'] else filters.fiscal_year.split('-')[1]
			
			salary_slip = frappe.db.sql(salary_slip_query, (
				filters.employee, 
				filters.company, 
				month_num,
				year,
				year
			))

			if salary_slip:
				amount = 0.0
				component_name = component.replace('<b>', '').replace('</b>', '')
				
				if component == "<b>Total Earning</b>":
					amount = get_total_earnings(salary_slip[0][0])
				elif component == "<b>Total Deduction</b>":
					amount = get_total_deductions(salary_slip[0][0])
				elif component == "<b>NET SALARY</b>":
					amount = get_net_salary(salary_slip[0][0])
				else:
					amount = get_component_amount(salary_slip[0][0], component_name)

				total[i] = format_amount(amount, component)
				sum_of_payments += amount

		total[-1] = format_amount(round(sum_of_payments, 1), "<b>")
		sum_of_payments = 0.0
		row_no += 1
		detail.append(total)
		
	return detail

def get_total_earnings(salary_slip):
	result = frappe.db.sql("""
		SELECT round(IFNULL(SUM(amount), 0), 1)
		FROM `tabSalary Detail`
		WHERE parent = %s 
		AND parentfield = 'earnings'
	""", salary_slip)
	return result[0][0] if result else 0.0

def get_total_deductions(salary_slip):
	result = frappe.db.sql("""
		SELECT round(IFNULL(SUM(amount), 0), 1)
		FROM `tabSalary Detail`
		WHERE parent = %s 
		AND parentfield = 'deductions'
	""", salary_slip)
	return result[0][0] if result else 0.0

def get_net_salary(salary_slip):
	result = frappe.db.sql("""
		SELECT 
			round(
				(SELECT IFNULL(SUM(amount), 0) FROM `tabSalary Detail` WHERE parent = %s AND parentfield = 'earnings') -
				(SELECT IFNULL(SUM(amount), 0) FROM `tabSalary Detail` WHERE parent = %s AND parentfield = 'deductions'),
				1
			)
	""", (salary_slip, salary_slip))
	return result[0][0] if result else 0.0

def get_component_amount(salary_slip, component):
	result = frappe.db.sql("""
		SELECT round(IFNULL(amount, 0), 1)
		FROM `tabSalary Detail`
		WHERE parent = %s 
		AND salary_component = %s
		AND parentfield IN ('earnings', 'deductions')
	""", (salary_slip, component))
	return result[0][0] if result else 0.0

def format_amount(amount, component):
	formatted = frappe.utils.fmt_money(str(amount))
	return f"<b>{formatted}</b>" if "<b>" in component else formatted

def format_amount(amount, component):
	formatted = frappe.utils.fmt_money(str(amount))
	return f"<b>{formatted}</b>" if "<b>" in component else formatted
