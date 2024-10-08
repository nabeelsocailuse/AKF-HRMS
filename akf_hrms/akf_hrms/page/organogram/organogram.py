import frappe

@frappe.whitelist()
def get_children(doctype, parent=None, company=None, is_root=False, is_tree=False):

	filters = [["status", "!=", "Left"]]
	filters.append(["company", "=", company])
	if parent and company and parent != company:
		filters.append(["reports_to", "=", parent])
	else:
		filters.append(["reports_to", "=", ""])
	
	# case_statement = """ case when image is not null then image else '' END as img".format(avatar) """
	
	first_level = frappe.db.get_list('Employee',
	fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else 'CEO' END as title","branch","cluster"],
	filters = filters,
	order_by="name")

	ultimate_nodes = []
	second_lev = []
	for emp in first_level:
		second_lev.append(frappe.get_list("Employee",
		fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
		filters=[["reports_to", "=", emp.id],["status", "!=", "Left"]],
		order_by="name"))
	second_level = []
	third_level = []
	fourth_level = []
	fifth_level = []
	sixth_level = []
	seventh_level = []
	eighth_level = []
	ninth_level = []
	tenth_level = []

	for i in second_lev:
		if len(i) > 0:
			second_level.append(i)
	for emp in first_level:
		ultimate_nodes.append(emp)
	for emp in second_level:
		if len(emp) == 1:
			ultimate_nodes.append(emp[0])
			third_level.append(frappe.get_list("Employee",
		fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
		filters=[["reports_to", "=", emp.id],["status", "!=", "Left"]],
		order_by="name"))
		elif len(emp) > 1:
			for em in emp:
				ultimate_nodes.append(em)
				third_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
			order_by="name"))
	for emp in third_level:
		if len(emp) == 1:
			ultimate_nodes.append(emp[0])
			fourth_level.append(frappe.get_list("Employee",
		fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
		filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
		order_by="name"))
		elif len(emp) > 1:
			for em in emp:
				ultimate_nodes.append(em)
				fourth_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
			order_by="name"))
	for emp in fourth_level:
		if len(emp) == 1:
			ultimate_nodes.append(emp[0])
			fifth_level.append(frappe.get_list("Employee",
		fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
		filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
		order_by="name"))
		elif len(emp) > 1:
			for em in emp:
				ultimate_nodes.append(em)
				fifth_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
			order_by="name"))
	if fifth_level:
		for emp in fifth_level:
			if len(emp) == 1:
				ultimate_nodes.append(emp[0])
				sixth_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
			order_by="name"))
			elif len(emp) > 1:
				for em in emp:
					ultimate_nodes.append(em)
					sixth_level.append(frappe.get_list("Employee",
				fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
				filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
				order_by="name"))
	if sixth_level:
		for emp in sixth_level:
			if len(emp) == 1:
				ultimate_nodes.append(emp[0])
				seventh_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
			order_by="name"))
			elif len(emp) > 1:
				for em in emp:
					ultimate_nodes.append(em)
					seventh_level.append(frappe.get_list("Employee",
				fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
				filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
				order_by="name"))
	if seventh_level:
		for emp in seventh_level:
			if len(emp) == 1:
				ultimate_nodes.append(emp[0])
				eighth_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
			order_by="name"))
			elif len(emp) > 1:
				for em in emp:
					ultimate_nodes.append(em)
					eighth_level.append(frappe.get_list("Employee",
				fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
				filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
				order_by="name"))
	if eighth_level:
		for emp in eighth_level:
			if len(emp) == 1:
				ultimate_nodes.append(emp[0])
				ninth_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
			order_by="name"))
			elif len(emp) > 1:
				for em in emp:
					ultimate_nodes.append(em)
					ninth_level.append(frappe.get_list("Employee",
				fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
				filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
				order_by="name"))
	if ninth_level:
		for emp in ninth_level:
			if len(emp) == 1:
				ultimate_nodes.append(emp[0])
				tenth_level.append(frappe.get_list("Employee",
			fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
			filters=[["reports_to", "=", emp[0].id],["status", "!=", "Left"]],
			order_by="name"))
			elif len(emp) > 1:
				for em in emp:
					ultimate_nodes.append(em)
					tenth_level.append(frappe.get_list("Employee",
				fields = ["employee_name as name", "name as id", "base64_image as img","reports_to as parentId", "case when designation is not null then designation else '-' END as title","branch","cluster"],
				filters=[["reports_to", "=", em.id],["status", "!=", "Left"]],
				order_by="name"))
	if tenth_level:
		for emp in tenth_level:
			if len(emp) == 1:
				ultimate_nodes.append(emp[0])
			
			elif len(emp) > 1:
				for em in emp:
					ultimate_nodes.append(em)
	return ultimate_nodes

@frappe.whitelist()
def convert_image_to_base64():
	import base64, requests
	base64_image = frappe.db.sql(""" select name, image
		from tabEmployee
		where status="Active"
	""", as_dict=1)
	for url in base64_image:
		image_path = url.image
		if image_path:
			if not image_path.startswith("http"):
				image_path = 'http://172.104.34.13:6001' + image_path
		else:
			image_path = 'http://172.104.34.13:6001' + "/files/male-avatar.png"
		# if not image_path.startswith('http'):
		# 	image_path = 'http://172.104.34.13:6001' + image_path
		# image_path   = "http://172.104.34.13:6001/files/Muhammad_Ejaz_Asif_Picture.jpg"
		my_string = base64.b64encode(requests.get(image_path).content)
		my_string = "data:image/png;base64,"+(my_string.decode("utf-8"))
		frappe.db.set_value("Employee", url.name, "base64_image", my_string)
	# return my_string

@frappe.whitelist()
def organo_dict():
	root = frappe.db.get_list("Employee", filters={"designation": "CEO"}, fields=["name", "employee_name", "designation", "branch", "reports_to as parentId", "base64_image", "cluster"])
	ultimate_nodes = []
	for d in root:
		root_employee = d.name
		ultimate_nodes.append({
			"name": d.employee_name,
			"id": d.name,
			"img": d.base64_image,  
			"parentId": d.reports_to,
			"title": d.designation,
			"branch": d.branch, 
			"cluster": d.cluster,
		})
	
	reports_to_employees =  get_reports_to_employees()
	next_level_employees = get_next_level_employees()
	
	# ultimate_nodes +=  [{
	# 		"name": d.name,
	# 		"id": d.id,
	# 		"img": d.img,  
	# 		"parentId": d.parentId,
	# 		"title": d.title,
	# 		"branch": d.branch, 
	# 		"cluster": d.cluster,
	# 	} for d in next_level_employees if root_employee == d.parentId]

	for reports in reports_to_employees:
		# temp_list = [{
		# 	"name": reports.name,
		# 	"id": reports.id,
		# 	"img": reports.img,  
		# 	"parentId": reports.parentId,
		# 	"title": reports.title,
		# 	"branch": reports.branch, 
		# 	"cluster": reports.cluster,
		# }]
		temp_list = [{
			"name": d.name,
			"id": d.id,
			"img": d.img,  
			"parentId": d.parentId,
			"title": d.title,
			"branch": d.branch, 
			"cluster": d.cluster,
		} for d in next_level_employees if (d.parentId == reports.parentId)]

		ultimate_nodes += temp_list
	
	return ultimate_nodes


@frappe.whitelist()
def get_reports_to_employees():
	result = frappe.db.sql(""" 
		select 
			employee_name as name, name as id, base64_image as img, reports_to as parentId, designation as title, branch, cluster
		from 
			tabEmployee
		where 
			status="Active" and reports_to is not null
		group by 
			reports_to		
		""", as_dict=1)
	return result


def get_next_level_employees():
	return frappe.db.sql(""" 
		select 
			employee_name as name, name as id, base64_image as img, reports_to as parentId, designation as title, branch, cluster

		from 
			tabEmployee
		where 
			status="Active"
		group by 
		reports_to, name
		""", as_dict=1)




""" 
{
	cluster: null, 
	img: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAgAA…/r6NkqB0BoDpvYR2l6R94PguGU+BoEAAAAABJRU5ErkJggg==', 
	parentId: null, 
	branch: 'Main Lab', 
	name: 'Dr. Naseer Ahmad',
	"title": "CEO"
}
"""
