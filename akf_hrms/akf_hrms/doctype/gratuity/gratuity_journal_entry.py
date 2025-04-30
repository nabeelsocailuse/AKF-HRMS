import frappe
from akf_hrms.akf_hrms.doctype.gratuity.gratuity import (
	get_gratuity_rule_config,	
	calculate_work_experience,
	calculate_gratuity_amount
)
from frappe.utils import getdate, fmt_money

# bench --site al-khidmat.com execute akf_hrms.akf_hrms.doctype.gratuity.gratuity_journal_entry.calculate_work_experience_and_amount
@frappe.whitelist()
def calculate_work_experience_and_amount(self=None):
	# self = frappe._dict({
	# 	"company": "Alkhidmat Foundation Pakistan",
	# 	"gratuity_rule": "Test",
	# 	"current_work_experience": 0,
	# 	"employee": "AHF-PK-CO-00001",
	# 	"name": "HR-GRA-PAY-00001"
	# })
	for self in frappe.db.sql("""
						Select name, employee, company,
						(select cost_center From `tabCompany` Where name=e.company) as cost_center,
						(select custom_gratuity_expense_account From `tabCompany` Where name=e.company) as gratuity_expense_account,
						(select custom_gratuity_payable_account From `tabCompany` Where name=e.company) as gratuity_payable_account
						From `tabEmployee` e
						Where docstatus=0
						and status='Active'
						and name ="AHF-PK-CO-00001"
	""", as_dict=1):
		self.update({
			"gratuity_rule": "Test"
		})
		rule = get_gratuity_rule_config(self.gratuity_rule)

		current_work_experience = (
			calculate_work_experience(self.employee, self.gratuity_rule) or 0
		)

		gratuity_amount = (
			calculate_gratuity_amount(
				self.employee, self.gratuity_rule, current_work_experience
			)
			or 0
		)
		self.update({
			"current_work_experience": current_work_experience,
			"amount": gratuity_amount,
		})
		create_journal_entry(self)
		frappe.msgprint(f"Journal entry created successfully!", alert=1)
	

def create_journal_entry(self):
    args = frappe._dict({
        "doctype": "Journal Entry",
		"entry_type": "Journal Entry",
		"company": self.company,
		"posting_date": getdate(),
		"accounts":[
			{
				"account": self.gratuity_payable_account,
				# "against_account": self.gratuity_payable_account,
				"cost_center": self.cost_center,
				"party_type": "Employee",
				"party": self.employee,
				"credit_in_account_currency": self.amount,			
				"credit": self.amount,
				# "reference_type": "Employee",
				# "reference_name": self.name,
   			},
			{
				"account": self.gratuity_expense_account,
				# "against_account": self.employee,
				"cost_center": self.cost_center,
				"party_type": "Employee",
				"party": self.employee,
				"debit_in_account_currency": self.amount,
				"debit": self.amount,
				# "reference_type": "Employee",
				# "reference_name": self.name,
   			}
		],
		"total_debit": self.amount,
		"total_credit": self.amount,
		"remark": f"Employee gratuity {fmt_money(self.amount)}",
	})
    doc = frappe.get_doc(args)
    # frappe.throw(frappe.as_json(doc))
    doc.insert(ignore_permissions=True)
    # doc.submit()