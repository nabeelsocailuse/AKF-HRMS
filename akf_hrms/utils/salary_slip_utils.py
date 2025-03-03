import frappe

def get_taxable_salary_percentage(company):
    return frappe.get_value(
			"Company",
			{"name": company, "custom_enable_taxable_percentage": 1},
			(
				"custom_taxable_salary_percentage"
			)
		)

# Nabeel Saleem, 11-02-2025
def get_salary_percent_taxable_amount(self, salary_component, amount):
    if (salary_component=="Basic"):
        taxable_salary_percentage = get_taxable_salary_percentage(self.company)
        if (taxable_salary_percentage):
            if (taxable_salary_percentage>0.0):
                    amount = self._salary_structure_assignment.base * (taxable_salary_percentage/100)
                    return amount
    return amount

# Nabeel Saleem, 12-02-2025
def get_pre_salary_percent_taxable_amount(
    company,
    employee,
    start_date,
    end_date,
    parentfield,
    salary_component=None,
    is_tax_applicable=None,
    is_flexible_benefit=0,
    exempted_from_income_tax=0,
    variable_based_on_taxable_salary=0,
    field_to_select="amount"
):
    ss = frappe.qb.DocType("Salary Slip")
    sd = frappe.qb.DocType("Salary Detail")

    if field_to_select == "amount":
        field = sd.amount
    else:
        field = sd.additional_amount
    query = (
        frappe.qb.from_(ss)
        .join(sd)
        .on(sd.parent == ss.name)
        .select(sd.parent,sd.salary_component, sd.amount)
        .where(sd.parentfield == parentfield)
        .where(sd.is_flexible_benefit == is_flexible_benefit)
        .where(ss.docstatus == 1)
        .where(ss.employee == employee)
        .where(ss.start_date.between(start_date, end_date))
        .where(ss.end_date.between(start_date, end_date))
    )
    result = query.run(as_dict=True)
    pre_taxable_earnings = 0.0
    for d in result:
        pre_taxable_earnings += get_salary_percent_taxable_amount(company, d.salary_component, d.amount)
        print(f"---pre_taxable_earnings: {pre_taxable_earnings}")
        print(f"d: {d}")
    return pre_taxable_earnings

# Nabeel Saleem, 11-02-2025
def get_income_tax_additional_salary(eval_locals):
	""" get_additional_salaries(employee, start_date, end_date, component_type) """
	
	if(eval_locals.employee and eval_locals.start_date and eval_locals.end_date):
		amount = frappe.db.get_value("Additional Salary", 
				{
                    "docstatus": 1,
					"salary_component": "Income Tax",
					"employee": eval_locals.employee, 
					"payroll_date": ["between", [eval_locals.start_date, eval_locals.end_date]]
		}, "amount") or None
		if(amount):
			return (amount)
	return None
