from datetime import datetime, timedelta
from dateutil import relativedelta

import frappe
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import (flt, month_diff, add_months, get_datetime)



# ==========================================
import erpnext
from erpnext.accounts.utils import get_fiscal_year
from frappe.query_builder.functions import Count, Sum
from hrms.payroll.doctype.payroll_period.payroll_period import (
	get_payroll_period,
	get_period_factor,
)
from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import (
	cancel_loan_repayment_entry,
	make_loan_repayment_entry,
	set_loan_repayment,
)

from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
# ========================================================

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
        self.set_social_security()
        self.get_set_takful_plan()
        self.set_eobi()
        # self.set_total_deduction_gross_pay()
        self.calculate_net_pay()
        self.compute_year_to_date()
        self.compute_month_to_date()
        self.compute_component_wise_year_to_date()


    @frappe.whitelist()
    def get_set_takful_plan(self):        
        employee = frappe.get_doc("Employee", {"name": self.employee}, ["name", "custom_takaful_plan"])
        if employee.custom_takaful_plan:           
            tk_plan = frappe.get_doc("Takaful Plan", {"name": employee.custom_takaful_plan}, ["employer_contribution", "employee_contibution"])
            # self.custom_takaful_plan_employer_contribution = tk_plan.employer_contribution
            for d in self.deductions:
                if d.salary_component == "Takaful Plan":
                    d.amount = float(tk_plan.employee_contribution)
            for e in self.earnings:
                if e.salary_component == "Takaful Plan Employer Contribution":
                    e.amount = float(tk_plan.employer_contribution)

    @frappe.whitelist()
    def set_eobi(self):
        # self.custom_eobi_employer_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employer_contribution")        
        employee = frappe.get_doc("Employee", {"name": self.employee}, ["name", "custom_eobi_applicable"])
        if employee.custom_eobi_applicable == 1:
            eobi_employee_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employee_contribution")
            eobi_employer_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employer_contribution")
            for d in self.deductions:
                if d.salary_component == "EOBI":
                    d.amount = float(eobi_employee_contribution)
            for e in self.earnings:
                if e.salary_component == "EOBI Employer Contribution":
                    e.amount = float(eobi_employer_contribution)

    @frappe.whitelist()
    def set_social_security(self):
        social_security_amount = frappe.db.get_value("AKF Payroll Settings", None, "social_security_amount")
        social_security_rate = frappe.db.get_value("AKF Payroll Settings", None, "social_security_rate")		
        
        if flt(self.gross_pay) <= flt(social_security_amount):                     
            ssa_gross_pay = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee, "docstatus":1}, "base")                    
            social_security_amount_deduction = flt(ssa_gross_pay) * flt(social_security_rate) 
            for d in self.deductions:
                if d.salary_component == "Social Security":
                    d.amount = float(social_security_amount_deduction)


    def calculate_net_pay(self):
        if self.salary_structure:
            self.calculate_component_amounts("earnings")

        # get remaining numbers of sub-period (period for which one salary is processed)
        if self.payroll_period:
            self.remaining_sub_periods = get_period_factor(
                self.employee,
                self.start_date,
                self.end_date,
                self.payroll_frequency,
                self.payroll_period,
                joining_date=self.joining_date,
                relieving_date=self.relieving_date,
            )[1]

        self.gross_pay = self.get_component_totals("earnings", depends_on_payment_days=1)
        self.base_gross_pay = flt(
            flt(self.gross_pay) * flt(self.exchange_rate), self.precision("base_gross_pay")
        )

        if self.salary_structure:
            self.calculate_component_amounts("deductions")

        set_loan_repayment(self)

        self.set_precision_for_component_amounts()
        self.set_net_pay()
        self.compute_income_tax_breakup()
    
    def set_precision_for_component_amounts(self):
        for component_type in ("earnings", "deductions"):
            for component_row in self.get(component_type):
                component_row.amount = flt(component_row.amount, component_row.precision("amount"))

    def set_net_pay(self):
        self.total_deduction = self.get_component_totals("deductions")
        self.base_total_deduction = flt(
            flt(self.total_deduction) * flt(self.exchange_rate), self.precision("base_total_deduction")
        )
        self.net_pay = flt(self.gross_pay) - (
            flt(self.total_deduction) + flt(self.get("total_loan_repayment"))
        )
        self.rounded_total = rounded(self.net_pay)
        self.base_net_pay = flt(flt(self.net_pay) * flt(self.exchange_rate), self.precision("base_net_pay"))
        self.base_rounded_total = flt(rounded(self.base_net_pay), self.precision("base_net_pay"))
        if self.hour_rate:
            self.base_hour_rate = flt(
                flt(self.hour_rate) * flt(self.exchange_rate), self.precision("base_hour_rate")
            )
        self.set_net_total_in_words()
    
    def set_net_total_in_words(self):
        doc_currency = self.currency
        company_currency = erpnext.get_company_currency(self.company)
        total = self.net_pay if self.is_rounding_total_disabled() else self.rounded_total
        base_total = self.base_net_pay if self.is_rounding_total_disabled() else self.base_rounded_total
        self.total_in_words = money_in_words(total, doc_currency)
        self.base_total_in_words = money_in_words(base_total, company_currency)
    
    def is_rounding_total_disabled(self):
        return cint(frappe.db.get_single_value("Payroll Settings", "disable_rounded_total"))
    
    def calculate_component_amounts(self, component_type):
        if not getattr(self, "_salary_structure_doc", None):
            self._salary_structure_doc = frappe.get_cached_doc("Salary Structure", self.salary_structure)

        self.add_structure_components(component_type)
        self.add_additional_salary_components(component_type)
        if component_type == "earnings":
            self.add_employee_benefits()
        else:
            self.add_tax_components()

    def add_structure_components(self, component_type):
        self.data, self.default_data = self.get_data_for_eval()
        timesheet_component = self._salary_structure_doc.salary_component

        for struct_row in self._salary_structure_doc.get(component_type):
            if self.salary_slip_based_on_timesheet and struct_row.salary_component == timesheet_component:
                continue

            amount = self.eval_condition_and_formula(struct_row, self.data)
            if struct_row.statistical_component:
                # update statitical component amount in reference data based on payment days
                # since row for statistical component is not added to salary slip

                self.default_data[struct_row.abbr] = flt(amount)
                if struct_row.depends_on_payment_days:
                    payment_days_amount = (
                        flt(amount) * flt(self.payment_days) / cint(self.total_working_days)
                        if self.total_working_days
                        else 0
                    )
                    self.data[struct_row.abbr] = flt(payment_days_amount, struct_row.precision("amount"))

            else:
                # default behavior, the system does not add if component amount is zero
                # if remove_if_zero_valued is unchecked, then ask system to add component row
                remove_if_zero_valued = frappe.get_cached_value(
                    "Salary Component", struct_row.salary_component, "remove_if_zero_valued"
                )

                default_amount = 0

                if (
                    amount
                    or (struct_row.amount_based_on_formula and amount is not None)
                    or (not remove_if_zero_valued and amount is not None and not self.data[struct_row.abbr])
                ):
                    default_amount = self.eval_condition_and_formula(struct_row, self.default_data)
                    self.update_component_row(
                        struct_row,
                        amount,
                        component_type,
                        data=self.data,
                        default_amount=default_amount,
                        remove_if_zero_valued=remove_if_zero_valued,
                    )

    def compute_income_tax_breakup(self):
        if not self.payroll_period:
            return

        self.standard_tax_exemption_amount = 0
        self.tax_exemption_declaration = 0
        self.deductions_before_tax_calculation = 0

        self.non_taxable_earnings = self.compute_non_taxable_earnings()

        self.ctc = self.compute_ctc()

        self.income_from_other_sources = self.get_income_form_other_sources()

        self.total_earnings = self.ctc + self.income_from_other_sources

        if hasattr(self, "tax_slab"):
            if self.tax_slab.allow_tax_exemption:
                self.standard_tax_exemption_amount = self.tax_slab.standard_tax_exemption_amount
                self.deductions_before_tax_calculation = (
                    self.compute_annual_deductions_before_tax_calculation()
                )

            self.tax_exemption_declaration = (
                self.get_total_exemption_amount() - self.standard_tax_exemption_amount
            )

        self.annual_taxable_amount = self.total_earnings - (
            self.non_taxable_earnings
            + self.deductions_before_tax_calculation
            + self.tax_exemption_declaration
            + self.standard_tax_exemption_amount
        )

        self.income_tax_deducted_till_date = self.get_income_tax_deducted_till_date()

        if hasattr(self, "total_structured_tax_amount") and hasattr(self, "current_structured_tax_amount"):
            self.future_income_tax_deductions = (
                self.total_structured_tax_amount - self.income_tax_deducted_till_date
            )

            self.current_month_income_tax = self.current_structured_tax_amount

            # non included current_month_income_tax separately as its already considered
            # while calculating income_tax_deducted_till_date

            self.total_income_tax = self.income_tax_deducted_till_date + self.future_income_tax_deductions

    def compute_ctc(self):
        if hasattr(self, "previous_taxable_earnings"):
            return (
                self.previous_taxable_earnings_before_exemption
                + self.current_structured_taxable_earnings_before_exemption
                + self.future_structured_taxable_earnings_before_exemption
                + self.current_additional_earnings
                + self.other_incomes
                + self.unclaimed_taxable_benefits
                + self.non_taxable_earnings
            )

        return 0.0

    def compute_year_to_date(self):
        year_to_date = 0
        period_start_date, period_end_date = self.get_year_to_date_period()

        salary_slip_sum = frappe.get_list(
            "Salary Slip",
            fields=["sum(net_pay) as net_sum", "sum(gross_pay) as gross_sum"],
            filters={
                "employee": self.employee,
                "start_date": [">=", period_start_date],
                "end_date": ["<", period_end_date],
                "name": ["!=", self.name],
                "docstatus": 1,
            },
        )

        year_to_date = flt(salary_slip_sum[0].net_sum) if salary_slip_sum else 0.0
        gross_year_to_date = flt(salary_slip_sum[0].gross_sum) if salary_slip_sum else 0.0

        year_to_date += self.net_pay
        gross_year_to_date += self.gross_pay
        self.year_to_date = year_to_date
        self.gross_year_to_date = gross_year_to_date

    def compute_month_to_date(self):
        month_to_date = 0
        first_day_of_the_month = get_first_day(self.start_date)
        salary_slip_sum = frappe.get_list(
            "Salary Slip",
            fields=["sum(net_pay) as sum"],
            filters={
                "employee": self.employee,
                "start_date": [">=", first_day_of_the_month],
                "end_date": ["<", self.start_date],
                "name": ["!=", self.name],
                "docstatus": 1,
            },
        )

        month_to_date = flt(salary_slip_sum[0].sum) if salary_slip_sum else 0.0

        month_to_date += self.net_pay
        self.month_to_date = month_to_date

    def compute_component_wise_year_to_date(self):
        period_start_date, period_end_date = self.get_year_to_date_period()

        ss = frappe.qb.DocType("Salary Slip")
        sd = frappe.qb.DocType("Salary Detail")

        for key in ("earnings", "deductions"):
            for component in self.get(key):
                year_to_date = 0
                component_sum = (
                    frappe.qb.from_(sd)
                    .inner_join(ss)
                    .on(sd.parent == ss.name)
                    .select(Sum(sd.amount).as_("sum"))
                    .where(
                        (ss.employee == self.employee)
                        & (sd.salary_component == component.salary_component)
                        & (ss.start_date >= period_start_date)
                        & (ss.end_date < period_end_date)
                        & (ss.name != self.name)
                        & (ss.docstatus == 1)
                    )
                ).run()

                year_to_date = flt(component_sum[0][0]) if component_sum else 0.0
                year_to_date += component.amount
                component.year_to_date = year_to_date

    def get_year_to_date_period(self):
        if self.payroll_period:
            period_start_date = self.payroll_period.start_date
            period_end_date = self.payroll_period.end_date
        else:
            # get dates based on fiscal year if no payroll period exists
            fiscal_year = get_fiscal_year(date=self.start_date, company=self.company, as_dict=1)
            period_start_date = fiscal_year.year_start_date
            period_end_date = fiscal_year.year_end_date

        return period_start_date, period_end_date
			
			
    