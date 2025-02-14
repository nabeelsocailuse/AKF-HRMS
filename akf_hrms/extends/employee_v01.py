import frappe, re
from frappe.model.document import Document
from erpnext.setup.doctype.employee.employee import Employee


class XEmployee(Employee):
	def validate(self):
		super().validate()
		self.verify_identity_card_no()
		self.set_base64_image()
  
	def verify_identity_card_no(self):
		details = get_country_details(self.custom_country)
		if (not details) or (not details.custom_id_regex) or (not self.custom_cnic): return
		if (not match_regex(details.custom_id_regex, self.custom_cnic)):
			exception_msg('Please enter valid %s.'%details.custom_label)

	def validate_salary_in_company_work_history(self):
		for row in self.internal_work_history:
			self.validate_normal_salary(row)
			self.validate_increment_amount(row)
	
	def validate_normal_salary(self, row):
		try:
			custom_salary = float(row.custom_salary)
			if (custom_salary < 0):
				frappe.throw(f"Row#{row.idx}: Salary cannot be negative.")
		except (ValueError, TypeError):
			frappe.throw(f"Row#{row.idx}: Invalid input for salary. Please enter a positive number.")
	
	def validate_increment_amount(self, row):
		try:
			custom_increment_amount = float(row.custom_increment_amount)
			if custom_increment_amount < 0:
				frappe.throw(f"Row#{row.idx}: Increment amount cannot be negative.")
		except (ValueError, TypeError):
			frappe.throw("Invalid input for increment amount. Please enter a positive number.")

	def set_base64_image(self):
		if (self.is_new()): return
		import base64, requests
		url = frappe.utils.get_url()
		image_path = self.image
		image_path = '{0}{1}'.format(url, image_path if(image_path) else "/assets/akf_hrms/images/blank-img.png")
		my_string = base64.b64encode(requests.get(image_path, verify=False).content)
		my_string = "data:image/png;base64,"+(my_string.decode("utf-8"))
		self.custom_base64_image = my_string
  
@frappe.whitelist()
def get_country_details(country):
	return frappe.db.get_value('Country', {'name': country}, ["custom_label", "custom_id_mask", "custom_id_regex"], as_dict=1)

def match_regex(regex ,mystr):
	return re.match(regex, mystr)

def exception_msg(msg):
	frappe.throw(msg)


def set_bulk_base64_image():
	import base64, requests
	url = frappe.utils.get_url()
	for d in frappe.db.get_list('Employee', filters={'status': 'Active', 'name': 'AKFP-PK-CO-00086'}, fields=['name', 'image']):
		try:
			image_path = d.image
			image_path = '{0}{1}'.format(url, image_path if(image_path) else "/assets/akf_hrms/images/blank-img.png")
			my_string = base64.b64encode(requests.get(image_path, verify=False).content)
			my_string = "data:image/png;base64,"+(my_string.decode("utf-8"))
			print(f"{d}")
			frappe.db.set_value('Employee', d.name, 'custom_base64_image', my_string, update_modified=False)
		except Exception:
			pass
        

def del_user_file_attachments():
    frappe.db.sql(""" delete 
            from `tabFile` 
            where 
            attached_to_docType='User' 
            and cast(creation as date) between DATE_SUB(CURDATE(), INTERVAL 5 MONTH) and CURDATE()  """)