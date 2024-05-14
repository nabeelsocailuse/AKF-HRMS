import frappe
from akf_hrms.json_format.country_json import get_country_json
def after_install():
    if(frappe.db.exists("DocType", {"name": "Country"})):
        countries_list = get_country_json()
        for country in countries_list:
            if(not frappe.db.exists("Country", country)):
                doc = frappe.new_doc("Country")
                doc.country_name = country.get("country_name")
                doc.date_format = country.get("date_format")
                doc.time_format = country.get("time_format")
                doc.time_zones = country.get("time_zones")
                doc.code = country.get("code")
                doc.custom_dial_code =  country.get("custom_dial_code")
                doc.custom_phone_mask = country.get("custom_phone_mask")
                doc.custom_phone_regex = country.get("custom_phone_regex")
                doc.custom_label = country.get("custom_label")
                doc.custom_id_mask = country.get("custom_id_mask")
                doc.custom_id_regex = country.get("custom_id_regex")
                doc.save()
            else:
                doc = frappe.get_doc("Country", country.get("country_name"))
                doc.date_format = country.get("date_format")
                doc.time_format = country.get("time_format")
                doc.time_zones = country.get("time_zones")
                doc.code = country.get("code")
                doc.custom_dial_code =  country.get("custom_dial_code")
                doc.custom_phone_mask = country.get("custom_phone_mask")
                doc.custom_phone_regex = country.get("custom_phone_regex")
                doc.custom_label = country.get("custom_label")
                doc.custom_id_mask = country.get("custom_id_mask")
                doc.custom_id_regex = country.get("custom_id_regex")
                doc.save()