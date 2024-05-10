# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe, ast
from frappe import _

@frappe.whitelist()
def get_policy(fargs):
	fargs = ast.literal_eval(fargs)
	total_policy_list = []
	get_policy_ = []

	if 'HR Manager' in frappe.get_roles(frappe.session.user):
		get_policy_ = frappe.db.sql("""select name, IFNULL(policy_contents,""), IFNULL(policy_file, "/desk#Form/Policy/Policy") from `tabEmployee Policy Management` 
						where status ='Active' %s order by sort_order"""%get_conditions(fargs), fargs)
		
	else:
		emp_company = frappe.db.sql("""select company from `tabEmployee` where status='Active' and user_id=%s """,(frappe.session.user))
		if emp_company:
			get_policy_ = frappe.db.sql("""select epm.name, IFNULL(epm.policy_contents,""), IFNULL(policy_file, "/desk#Form/Policy/Policy") 
						from `tabEmployee Policy Management` as epm, `tabFiscal Year Company` as fyc 
						where epm.status ='Active'  and fyc.parent=epm.name and fyc.company=%s %s order by sort_order""",(emp_company[0][0], get_conditions(fargs)), fargs)
	
	if get_policy_:
		for x in get_policy_:
			dictt = { "policy_contents":"None", "name":"None", "policy_file":"None" }
			dictt["name"] = x[0]
			dictt["policy_contents"] = x[1]
			dictt["policy_file"] = x[2]
			total_policy_list.append(dictt)
	
	return total_policy_list

def get_conditions(fargs):
	conditions = " and custom_department=%(department)s" if(fargs.get("department")) else ""
	return conditions