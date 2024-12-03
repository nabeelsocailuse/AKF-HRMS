import frappe, re

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

    image_path = self.image
    url = frappe.utils.get_url()
    
    if image_path:
        image_path = f'{url}{image_path}' 
    else:
        image_path = f"{url}/assets/akf_hrms/images/blank-img.png"

    my_string = base64.b64encode(requests.get(image_path).content)
    my_string = "data:image/png;base64,"+(my_string.decode("utf-8"))
    self.custom_base64_image = my_string



@frappe.whitelist()
def get_country_details(country):
	return frappe.db.get_value('Country', {'name': country}, ["custom_label", "custom_id_mask", "custom_id_regex"], as_dict=1)

def match_regex(regex ,mystr):
	return re.match(regex, mystr)

def exception_msg(msg):
	frappe.throw(msg)

