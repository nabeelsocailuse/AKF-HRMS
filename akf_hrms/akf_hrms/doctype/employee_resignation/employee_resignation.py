# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class EmployeeResignation(Document):
	def validate(self):
		self.resignation_date_format = frappe.utils.formatdate(self.resignation_date, "dd-MMM-yyyy")
		if self.employee and self.resignation_date and self.employment_type and not self.last_working_day:
			self.last_working_day = get_last_working_day(self.resignation_date, self.employment_type)
		self.last_working_day_format = frappe.utils.formatdate(self.last_working_day, "dd-MMM-yyyy")
		self.validate_duplicate_employee_resignation()
		# self.send_mail_on_workflow_action()
		# self.add_reliving_date_in_emp_table()
		
	def validate_duplicate_employee_resignation(self):
		emp_resignation = frappe.db.exists(
			"Employee Resignation", {"employee": self.employee, "docstatus": ("!=", 2)}
		)
		if emp_resignation and emp_resignation != self.name:
			frappe.throw(
				_("Employee Resignation: {0} already exists for Employee: {1}").format(
					frappe.bold(emp_resignation), frappe.bold(self.employee)
				)
			)

	def add_reliving_date_in_emp_table(self):
		if self.workflow_state == "Approved by HR":
			frappe.db.set_value("Employee" ,self.employee ,'relieving_date', self.last_working_day)
			self.cancel_leave_allocation()
	def cancel_leave_allocation(self):
		get_allocation = frappe.db.sql("""select name from `tabLeave Allocation` where docstatus=1 
							and employee=%s """,(self.employee))
		if get_allocation:
			for allocation in get_allocation:
				doc = frappe.get_doc("Leave Allocation", allocation[0])
				doc.cancel()
	def send_mail_on_workflow_action(self):
		if self.workflow_state == "Approved by HR":
			if (self.gender == "Male"):
				gender_chk = 'Mr. ' + str(self.employee_name)
				gender_chk_ = 'his' 
			else:
				gender_chk = 'Miss. ' + str(self.employee_name)
				gender_chk_ = 'her'
			message_ = """Team Members,<br>HR department accept the Resignation letter of <b>""" + str(gender_chk) + "</b> (" + str(self.department) + """) which received on """ + str(self.resignation_date_format) + """ and """ + str(gender_chk_) + """ last working day will be <b>""" + str(self.last_working_day_format) + """</b> in company.<br>"""
			chk_emp_inventory_sheet = frappe.db.sql("""select inv_tab.parent, inv.item_type, IFNULL(inv.item_name ,''), 
								inv.branch, IFNULL(inv.product_specification)	 
								from `tabEmployee Inventory Sheet` inv,`tabEmployee Inventory Sheet Table` inv_tab
								where inv_tab.employee=%s and inv_tab.status ='Assigned' and inv.name=inv_tab.parent
								""",(self.employee))
			if chk_emp_inventory_sheet:
				message_ += str(gender_chk) + """ have following company properties so please process collection as per company SOPs within due time.<br><br> <table  width="85%" cellpadding="5" cellspacing="0" style="border: 1px solid #000000; border-spacing: 1px; border-collapse: collapse; table-layout:fixed;"> <tr style="font-size:14px; background-color:#eee;">
			<th  colspan="7">Inventory Detail</th>
		</tr> 
		<tr class="ptr"> <td style="border:1px dotted #000000;text-align:center" colspan="1"><b>Inventory ID</b></td>
				<td style="border:1px dotted #000000;text-align:center" colspan="1"><b>Item Type</b></td>
				<td style="border:1px dotted #000000;text-align:center" colspan="1"><b>Item Name</b></td>
				<td style="border:1px dotted #000000;text-align:center" colspan="1"><b>Branch</b></td>
				<td style="border:1px dotted #000000;text-align:center" colspan="3"><b>Product Specification</b></td>
		</tr>"""
				for inventory in chk_emp_inventory_sheet:
					message_ += """<tr class="ptr">
								<td style="border:1px dotted #000000;text-align:center" colspan="1">""" + str(inventory[0]) + """</td>
								<td style="border:1px dotted #000000;text-align:center" colspan="1">""" + str(inventory[1]) + """</td>
								<td style="border:1px dotted #000000;text-align:center" colspan="1">""" + str(inventory[2]) + """</td>
								<td style="border:1px dotted #000000;text-align:center" colspan="1">""" + str(inventory[3]) + """</td>
								<td style="border:1px dotted #000000;text-align:center" colspan="3">""" + str(inventory[4]) + """</td>
							</tr>"""
				message_ += "</table>"
			frappe.sendmail(
				recipients=['ops.team@micromerger.com', 'finance.team@micromerger.com', 'hr@micromerger.com'],
				sender = "MM HR Department <xperterp@micromerger.com>",
				
				bject='Employee Resignation from ' + str(self.employee_name),
				message = _(message_)
			)
			
@frappe.whitelist()
def get_last_working_day(resignation_date = None, employment_type=None):
	return_date = None
	if employment_type and resignation_date:
		get_days = frappe.db.get_value("Employment Type", str(employment_type), "resignation_days")
		return_date = frappe.utils.add_days(resignation_date, get_days)
	return return_date
