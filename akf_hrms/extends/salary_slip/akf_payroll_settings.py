from datetime import datetime, timedelta
from dateutil import relativedelta

import frappe
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import (flt, month_diff, add_months, get_datetime)

class XSalarySlip(SalarySlip):
    
    def validate(self):
        super(XSalarySlip, self).validate()
        self.validate_other_info()
        self.get_eobi_pf_social_security_details()
    
    def validate_other_info(self):
        self.custom_pf_eligibility = self.start_date
        employment_type = frappe.get_value("Employee", self.employee, "employment_type")
        date_of_joining = frappe.get_value("Employee", self.employee, "date_of_joining")
        if employment_type == "Regular":
            # if get_datetime(date_of_joining) < get_datetime(add_months(self.start_date, -6)):
            if month_diff(self.start_date, date_of_joining)>6:
                self.custom_pf_deduction = "Yes"
                self.custom_pf_start_month = add_months(date_of_joining, 6)
                pf_list = []
                for d in self.deductions:
                    pf_list.append(d.salary_component)
                
                if ("Provident Fund" not in pf_list) and (self.pf_employer_contribution>0):
                    self.append("deductions",{
                        "salary_component":"Provident Fund",
                        "amount": self.pf_employer_contribution
                    })
                    self.total_deduction = self.total_deduction + self.pf_employer_contribution
            else:
                self.custom_pf_deduction = "No"
                self.pf_employer_contribution = 0
        else:
            self.pf_employer_contribution = 0
        
        if get_datetime(date_of_joining) < get_datetime(add_months(self.start_date, -6)):
            if get_datetime(date_of_joining) < get_datetime(add_months(self.start_date, -12)):
                self.custom_summer_break = "Paid as Usual"
            else:
                self.custom_summer_break = "Hold"
        else:
            self.custom_summer_break = "N/A"

        d1 = str(self.start_date).split("-")
        d2 = str(date_of_joining).split("-")
        date1 = datetime(int(d1[0]), int(d1[1]), int(d1[2]))
        date2 = datetime(int(d2[0]), int(d2[1]), int(d2[2]))

        diff = relativedelta.relativedelta(date1, date2)

        years_ = diff.years
        months_ = diff.months
        days_ = diff.days

        self.custom_summer_break_eligibility = '{} years, {} months, {} days'.format(years_, months_, days_)
        self.custom_service_duration_for_6_months_pf_eligibility = '{} years, {} months, {} days'.format(years_, months_, days_)
         
    @frappe.whitelist()
    def get_eobi_pf_social_security_details(self):  
        
    # Validate EOBI Employer Contribution
        self.custom_eobi_employer_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employer_contribution")
        
    # Validate EOBI Employee Contribution
        eobi_employee_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employee_contribution")
        for d in self.deductions:
            if d.salary_component == "EOBI":
                d.amount = eobi_employee_contribution
				
    # Validate Provident Employee/Employer Contribution
        date_of_joining = frappe.db.get_value("Employee", {"name": self.employee}, "date_of_joining")
        delay_of_provident_fund_deduction = frappe.db.get_value("AKF Payroll Settings", None, "delay_of_provident_fund_deduction")
        delay_months = 30*int(delay_of_provident_fund_deduction)
        if date_of_joining:
            delay_limit = datetime.now().date() - timedelta(days=delay_months)
            if date_of_joining < delay_limit:
                pf_employer_contribution_percent = frappe.db.get_value("AKF Payroll Settings", None, "provident_employer_contribution_percent")
                self.custom_provident_fund_employer_contribution = (float(self.gross_pay) * float(pf_employer_contribution_percent))/100.0
                
                pf_employee_contribution_percent = frappe.db.get_value("AKF Payroll Settings", None, "provident_employee_contribution_percent")
                provident_fund_employee_contribution = (float(self.gross_pay) * float(pf_employee_contribution_percent))/100.0
                for d in self.deductions:
                    if d.salary_component == "Provident Fund":
                        d.amount = provident_fund_employee_contribution

        # Validate Social Security
        social_security_amount = frappe.db.get_value("AKF Payroll Settings", None, "social_security_amount")
        social_security_rate = frappe.db.get_value("AKF Payroll Settings", None, "social_security_rate")		
        
        if flt(self.gross_pay) <= flt(social_security_amount):                     
            ssa_gross_pay = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee, "docstatus":1}, "base")                    
            social_security_amount_deduction = flt(ssa_gross_pay) * flt(social_security_rate) 
            for d in self.deductions:
                if d.salary_component == "Social Security":
                    d.amount = social_security_amount_deduction

        self.get_set_takful_plan()

    @frappe.whitelist()
    def get_set_takful_plan(self):
        # Validate Takaful Plan Employee/Employer Contribution
        employee = frappe.get_doc("Employee", {"name": self.employee}, ["name", "custom_takaful_plan"])
        if employee.custom_takaful_plan:
            # frappe.msgprint(frappe.as_json(employee))
            tk_plan = frappe.get_doc("Takaful Plan", {"name": employee.custom_takaful_plan}, ["employer_contribution", "employee_contibution"])
            self.custom_takaful_plan_employer_contribution = tk_plan.employer_contribution
            for d in self.deductions:
                if d.salary_component == "Takaful Plan":
                    d.amount = tk_plan.employee_contribution
			
			
    