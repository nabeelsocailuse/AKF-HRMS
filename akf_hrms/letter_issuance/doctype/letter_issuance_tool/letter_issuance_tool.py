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
#from PyPDF2 import PdfFileWriter
from frappe.utils.background_jobs import enqueue
import ast

class LetterIssuanceTool(Document):
	pass

@frappe.whitelist()
def issuance_tool_function(series, employees, letter_template, letter_head=None, attach_to_employee=None, print_format=None, type_=None, bulk_download=None):
	if letter_head and letter_head == '1':
		no_letter_head = 0
	else:
		no_letter_head = 1

	if print_format:
		pass
	else:
		print_format = 'Standard' #'Employee Letter'
	download_ = 0
	if bulk_download and bulk_download == '1':
		download_ = 1 
	letter_names = []
	employees_list = json.loads(employees)
	if employees_list:
		if letter_template and series:
			template_query = """ select name1, letter_content from `tabLetter Template` where name1 = '%s' """%(letter_template)
			template_data = frappe.db.sql(template_query)
			count = 0
			series_count = 1
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
					code_length = len(str(emp['employee']).split("-"))
					if code_length == 2:
						message = str(message).replace("{{ employee_code }}", str(emp['employee']).split("-")[1])
					else:
						message = str(message).replace("{{ employee_code }}", str(emp['employee']).split("-")[2])						
					message = str(message).replace("{{ today_date }}", frappe.utils.formatdate(frappe.utils.nowdate(), "dd-MMM-yyyy"))
					message = str(message).replace("{{ series }}", str(series_count).zfill(4))
					hr_sign = frappe.db.get_value("Employee", "EMP-MM-00075", "custom_hr_signature")
					message = str(message).replace("{{ custom_hr_signature }}", str(hr_sign))
					get_emp_sal = frappe.db.sql("""select base from `tabSalary Structure Assignment` where employee=%s and docstatus = 1 order by 
										name desc""",(emp['employee']))
					if get_emp_sal:
						message = str(message).replace("{{ salary }}", frappe.utils.fmt_money(get_emp_sal[0][0]))
					else:
						message = str(message).replace("{{ salary }}", "0.0")
					letter.actual_content = message
					letter.save()
					#---------- PDF ---------#
					#output = PdfFileWriter()
					# output = frappe.get_print("Employee Letter", employee_letter_name, print_format, doc=None, no_letterhead=no_letter_head, as_pdf = True)
					file_name = "{0}-{1}.pdf".format(employee_letter_name,emp['employee'])
					file = os.path.join(frappe.get_site_path('public', 'files'),"files" ,"letters" ,file_name)
					#output.write(open(file,"wb"))
					series_count += 1
					
					if attach_to_employee and attach_to_employee == '1':
						letter.attached_file = "/files/files/letters/"+employee_letter_name+"-"+emp['employee']+".pdf"
						file_path_for_email = "/public/files/files/letters/"+employee_letter_name+"-"+emp['employee']+".pdf"
						letter.attached_file_name = employee_letter_name+"-"+emp['employee']+".pdf"
						letter.save() #ignore_permissions = True
						#requests.get("http://localhost/files/letters/VFS-00002-HR-EMP-00002.pdf")
					else:
						letter.attached_file_name = employee_letter_name+"-"+emp['employee']+".pdf"
						letter.save() #ignore_permissions = True
					message_ = 'Please see attachment'
					if str(args.department) == 'TPFM - TCV - T':
						message_ = "Dear <b>"+ str(args.employee_name) +"</b>,<br>Please find attached your employment contract with MicroMerger for the term of one month TPFM - TCV campaign.<br><br>You are required to sign and then forward the signed contract to <b>hr@micromerger.com</b> before <b>06-October-2022</b>"
					if type_ == 'Email':
						user_ = emp['user_id'] #frappe.db.get_value("Employee", emp['employee'], "prefered_email")
						if user_:
							frappe.sendmail(
								recipients = [str(user_)],
								sender = "MM HR Department <xperterp@micromerger.com>",
								subject = '{0} - {1}'.format(letter_template,emp['employee']),
								message = _(message_),
								attachments = [frappe.attach_print('Employee Letter', letter.name, file_name=str(letter.name))]
							)						
					elif type_ == 'PDF':
						letter_names.append(letter.name)
					else:
						letter_names.append(letter.name)
						user_ = emp['user_id'] #frappe.db.get_value("Employee", emp['employee'], "prefered_email")
						if user_:
							frappe.sendmail(
								recipients = [str(user_)],
								sender = "MM HR Department <xperterp@micromerger.com>",
								subject = '{0} - {1}'.format(letter_template,emp['employee']),
								message = _(message_),
								attachments = [frappe.attach_print('Employee Letter', letter.name, file_name=str(letter.name))]
							)
			frappe.msgprint(str(count) + " Records Created.")
		else:
			frappe.throw(_("Please Select Mandatory Fields."))
	else:
		frappe.throw(_("Please add Employees."))
	ltr_list = []
	list_ = []
	val = 1
	if download_ == 1:
		if len(letter_names) > 8:
			for ltr in letter_names:
				if val % 8 == 0:
					list_.append(ltr)
					ltr_list.append(list_)
					list_ = []
				else:
					list_.append(ltr)
				val += 1
			ltr_list.append(list_)
		else:
			for ltr in letter_names:
				list_.append(ltr)
			ltr_list.append(list_)
	else:
		for ltr in letter_names:
			ltr_list.append([ltr])
	return ltr_list

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
