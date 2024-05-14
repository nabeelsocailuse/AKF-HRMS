# -*- coding: utf-8 -*-
# Copyright (c) 2020, publisher and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os
from frappe import msgprint, _
from frappe.model.document import Document
import json
import requests
from frappe.utils.pdf import get_pdf
from PyPDF2 import PdfFileWriter
from frappe.utils.background_jobs import enqueue
import ast

class LetterIssuanceTool(Document):
	def get_employees(self):
		emp_list = []
		list_ = []
		val = 1
		if self.bulk_download:
			if len(self.employees) > 10:
				for emp in self.employees:
					if val % 10 == 0:
						list_.append(emp.employee)
						emp_list.append(list_)
						list_ = []
					else:
						list_.append(emp.employee)
					val += 1
				emp_list.append(list_)
			else:
				for emp in self.employees:
					list_.append(emp.employee)
				emp_list.append(list_)
		else:
			for emp in self.employees:
				emp_list.append([emp.employee])
		frappe.throw(frappe.as_json(emp_list))
		return emp_list

@frappe.whitelist()
def issuance_tool_function(series, employees, letter_template, letter_head, send_email, attach_to_employee, print_format):
	if letter_head and letter_head == '1':
		no_letter_head = 0
	else:
		no_letter_head = 1

	if print_format:
		pass
	else:
		print_format = 'Standard' #'Employee Letter'
	
	letter_names = []
	employees_list = json.loads(employees)
	if employees_list:
		if letter_template and series:
			template_query = """ select name1, letter_content from `tabLetter Template` where name1 = '%s' """%(letter_template)
			template_data = frappe.db.sql(template_query)
			count = 0
			for emp in employees_list:
				if emp['employee']:
					count = count + 1
					#========= Create New Record in "Employee Letter" doctype
					letter = frappe.new_doc("Employee Letter")
					letter.naming_series = series
					letter.letter_template = letter_template
					letter.employee = emp['employee']
					letter.employee_name = emp['full_name']
					letter.designation = emp['designation']
					if template_data:
						letter.letter = template_data[0][1]
					letter.save() #ignore_permissions = True
					employee_letter_name = letter.name

					email_template = frappe.get_doc("Letter Template", letter_template)
					parent_doc = frappe.get_doc('Employee', emp['employee'])
					args = parent_doc.as_dict()
					args['letter_series'] = employee_letter_name
					message = frappe.render_template(email_template.letter_content, args)
					letter.actual_content = message
					letter.save()

					#---------- PDF ---------#
					output = PdfFileWriter()
					output = frappe.get_print("Employee Letter", employee_letter_name, print_format, doc=None, no_letterhead=no_letter_head, as_pdf = True, output = output)
					file_name = "{0}-{1}.pdf".format(employee_letter_name,emp['employee'])
					file = os.path.join(frappe.get_site_path('public', 'files'),"letters" ,file_name)
					output.write(open(file,"wb"))

					if attach_to_employee and attach_to_employee == '1':
						letter.attached_file = "/files/letters/"+employee_letter_name+"-"+emp['employee']+".pdf"
						file_path_for_email = "/public/files/letters/"+employee_letter_name+"-"+emp['employee']+".pdf"
						letter.attached_file_name = employee_letter_name+"-"+emp['employee']+".pdf"
						letter.save() #ignore_permissions = True
						#requests.get("http://localhost/files/letters/VFS-00002-HR-EMP-00002.pdf")
					else:
						letter.attached_file_name = employee_letter_name+"-"+emp['employee']+".pdf"
						letter.save() #ignore_permissions = True

					#---------- Send Email ---------#
					if send_email == '1':
						frappe.msgprint("send email")
						receiver = frappe.db.get_value("Employee", emp['employee'], "prefered_email")
						frappe.msgprint(frappe.as_json(frappe.attach_print('Employee Letter', 'abc00006', file_name='abc00006')))
						frappe.sendmail(
							recipients = ['u.farooq@micromerger.com'],
							sender = "MM HR Department <xperterp@micromerger.com>",
							subject = '{0} - {1}'.format(letter_template,emp['employee']),
							message = _("Please see attachment"),
							attachments = [frappe.attach_print('Employee Letter', 'abc00006', file_name='abc00006')]
						)						
					else:
						frappe.msgprint("just print")
						letter_names.append(letter.name)
			if send_email == '1':
				frappe.msgprint(str(count) + " Records Created and Email Sent.")
			else:
				frappe.msgprint(str(count) + " Records Created.")
		else:
			frappe.throw(_("Please Select Mandatory Fields."))
	else:
		frappe.throw(_("Please add Employees."))
	return employees

@frappe.whitelist()
def get_employees_data(company=None,branch=None,designation=None,department=None,args_value=None):
	where = ""
	if company and company!=" ":
		where = " and `tabEmployee`.company = '" + company + "'"
	if branch and branch!=" ":
		where += " and `tabEmployee`.branch = '" + branch + "'"
	if designation and designation!=" ":
		where += " and `tabEmployee`.designation = '" + designation + "'"
	if department and department!=" ":
		where += " and `tabEmployee`.department = '" + department + "'"
	conditions = ""
	args_va = ast.literal_eval(args_value)

	for key in args_va:
		if str(key[1]) in ['=','!=','like','not like','<','>','<=','>=','Between']:
			if key[1] == 'Between':
				conditions = conditions + " and "+ str(key[0]) + " " + str(key[1]) + " '" + str(key[2][0]) + "' and '" + str(key[2][1]) + "'"
			else:
				conditions = conditions + " and "+ str(key[0]) + " " + str(key[1]) + " '" + str(key[2]) + "'"

	query_e = """select employee, employee_name, user_id, designation, date_of_joining from `tabEmployee` where docstatus='0' {0} {1}""".format(conditions,where)

	employee_list = frappe.db.sql(query_e)

	return employee_list
