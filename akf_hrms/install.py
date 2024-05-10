import frappe
from akf_hrms.json_format.country_json import get_country_json
def after_install():
    if(frappe.db.exists("DocType", {"name": "Country"})):
        countries_list = get_country_json()
        for country in countries_list:
            if(not frappe.db.exists("Country", country)):
                frappe.get_doc("Country", country).insert()