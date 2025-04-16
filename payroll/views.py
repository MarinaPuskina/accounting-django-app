from django.views.generic import UpdateView, CreateView, TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import EmployeeSalary
from employees.models import Employee
from django import forms
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero, DivisionUndefined
from django.urls import reverse_lazy
from django.contrib.sessions.backends.db import SessionStore


def safe_decimal_division(numerator, denominator):
    try:
        if Decimal(str(denominator)) == 0:
            raise ValueError("Деление на ноль")
        return (Decimal(str(numerator)) / Decimal(str(denominator))).quantize(Decimal('0.01'), ROUND_HALF_UP)
    except (DivisionByZero, DivisionUndefined):
        raise ValueError("Ошибка при делении")


class TimeSheetForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Сотрудник'
    )
    month = forms.ChoiceField(
        choices=[
            (1, 'Январь'), (2, 'Февраль'), (3, 'Март'),
            (4, 'Апрель'), (5, 'Май'), (6, 'Июнь'),
            (7, 'Июль'), (8, 'Август'), (9, 'Сентябрь'),
            (10, 'Октябрь'), (11, 'Ноябрь'), (12, 'Декабрь')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Месяц'
    )
    year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Год',
        initial=2025
    )
    days_worked = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Количество отработанных дней'
    )
    schedule_days = forms.DecimalField(
        max_digits=5,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Количество дней по графику'
    )
    rate_1 = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Ставка 1 разряда'
    )
    tariff_coef = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Тарифный коэффициент'
    )

    percent_experience = forms.IntegerField(  # изменить с DecimalField на IntegerField
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Процент за стаж'
    )

    increase_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Процент повышения'
    )
    contract_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Процент по контракту'
    )
    bonus = forms.DecimalField(
        max_digits=5,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Премия'
    )

    sick_days = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Количество дней по больничному',
        initial=0
    )

    vacation_days = forms.DecimalField(
        max_digits=5,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Количество дней отпуска',
        initial=0
    )

    maternity_days = forms.DecimalField(
        max_digits=5,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Количество дней матери',
        initial=0
    )
    unpaid_days = forms.DecimalField(
        max_digits=5,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Количество дней за свой счет',
        initial=0
    )
    daily_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Средний дневной заработок'
    )
    tax_deduction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Налоговый вычет',
        initial=0
    )
    material_assistance = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Материальная помощь',
        initial=0
    )
    health_payment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Выплаты на оздоровление',
        initial=0
    )

    class Meta:
        model = EmployeeSalary
        fields = ['employee', 'month', 'year', 'rate_1', 'tariff_coef',
                  'increase_percent', 'contract_percent', 'percent_experience',
                  'days_worked', 'schedule_days', 'sick_days',
                  'vacation_days', 'maternity_days', 'unpaid_days', 'daily_rate', 'bonus',
                  'tax_deduction', 'health_payment', 'material_assistance']


class SalaryView(CreateView):
    model = EmployeeSalary
    form_class = TimeSheetForm
    template_name = 'payroll/salary_view.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            print("Входные данные:")
            print(f"rate_1: {form.cleaned_data['rate_1']}, тип: {type(form.cleaned_data['rate_1'])}")
            print(f"tariff_coef: {form.cleaned_data['tariff_coef']}, тип: {type(form.cleaned_data['tariff_coef'])}")
            TWOPLACES = Decimal('0.01')

            base = (Decimal(str(form.cleaned_data['rate_1'])) *
                    Decimal(str(form.cleaned_data['tariff_coef']))).quantize(TWOPLACES, ROUND_HALF_UP)
            increase = (base * (Decimal(str(form.cleaned_data['increase_percent'])) /
                                Decimal('100'))).quantize(TWOPLACES, ROUND_HALF_UP)
            contract = (base * (Decimal(str(form.cleaned_data['contract_percent'])) /
                                Decimal('100'))).quantize(TWOPLACES, ROUND_HALF_UP)
            total_salary = (base + increase + contract).quantize(TWOPLACES)
            final_salary = (total_salary * (Decimal(str(form.cleaned_data['days_worked'])) /
                                            Decimal(str(form.cleaned_data['schedule_days'])))).quantize(TWOPLACES,
                                                                                                        ROUND_HALF_UP)
            bonus_service = (final_salary * (Decimal(str(form.cleaned_data['percent_experience'])) /
                                             Decimal('100'))).quantize(TWOPLACES, ROUND_HALF_UP)

            # Сохраняем расчеты в модель
            self.object.total_salary = total_salary
            self.object.final_salary = final_salary
            self.object.bonus_service = bonus_service

            self.object.sick_pay = (Decimal(str(form.cleaned_data['daily_rate'])) *
                                    Decimal(str(form.cleaned_data['sick_days']))).quantize(TWOPLACES, ROUND_HALF_UP)

            salary_12_months = self.object.get_salary_12_months()
            average_daily = (Decimal(str(salary_12_months)) / Decimal('29.6')).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.vacation_pay = (average_daily *
                                        Decimal(str(form.cleaned_data['vacation_days']))).quantize(TWOPLACES,
                                                                                                   ROUND_HALF_UP)

            daily_rate = (total_salary / Decimal(str(form.cleaned_data['schedule_days']))).quantize(TWOPLACES,
                                                                                                    ROUND_HALF_UP)
            self.object.maternity_pay = (daily_rate *
                                         Decimal(str(form.cleaned_data['maternity_days']))).quantize(TWOPLACES,
                                                                                                     ROUND_HALF_UP)

            self.object.unpaid_pay = (Decimal(str(form.cleaned_data['daily_rate'])) *
                                      Decimal(str(form.cleaned_data['unpaid_days']))).quantize(TWOPLACES, ROUND_HALF_UP)


            total_accrued = (final_salary + bonus_service + self.object.sick_pay +
                             self.object.vacation_pay + self.object.maternity_pay +
                             Decimal(str(form.cleaned_data['bonus']))).quantize(TWOPLACES, ROUND_HALF_UP)

            self.object.tax_deduction = Decimal(str(form.cleaned_data['tax_deduction'])).quantize(TWOPLACES,
                                                                                                  ROUND_HALF_UP)
            taxable_income = (total_accrued - self.object.tax_deduction).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.income_tax = (taxable_income * Decimal('0.13')).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.pension_fund = (total_accrued * Decimal('0.01')).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.union_fee = (total_accrued * Decimal('0.01')).quantize(TWOPLACES, ROUND_HALF_UP)

            print(f"Base: {base}")
            print(f"Increase: {increase}")
            print(f"Contract: {contract}")
            print(f"Total salary: {total_salary}")

            self.object.save()
            return redirect('payroll:salary_detail', pk=self.object.pk)
        except Exception as e:
            print(f"Ошибка при сохранении: {str(e)}")
            messages.error(self.request, f"Ошибка в расчетах: {str(e)}")
            return self.form_invalid(form)


class SalaryEditView(UpdateView):
    model = EmployeeSalary
    form_class = TimeSheetForm
    template_name = 'payroll/salary_edit.html'
    success_url = '/payroll/salary-report/'

    def get_initial(self):
        initial = super().get_initial()
        obj = self.get_object()
        initial.update({
            'employee': obj.employee,
            'month': obj.month,
            'year': obj.year,
            'days_worked': obj.days_worked,
            'schedule_days': obj.schedule_days,
            'rate_1': obj.rate_1,
            'tariff_coef': obj.tariff_coef,
            'percent_experience': obj.percent_experience,
            'increase_percent': obj.increase_percent,
            'contract_percent': obj.contract_percent,
            'bonus': obj.bonus,
            'sick_days': obj.sick_days,
            'vacation_days': obj.vacation_days,
            'maternity_days': obj.maternity_days,
            'unpaid_days': obj.unpaid_days,
            'daily_rate': obj.daily_rate,
            'material_assistance': obj.material_assistance,
            'health_payment': obj.health_payment,
            'tax_deduction': obj.tax_deduction,
        })
        return initial

    def get_success_url(self):
        return reverse_lazy('payroll:salary_report')

    def form_valid(self, form):
        try:
            TWOPLACES = Decimal('0.01')
            print("Форма валидна, данные:", form.cleaned_data)
            self.object = form.save(commit=False)

            base = (Decimal(str(form.cleaned_data['rate_1'])) *
                    Decimal(str(form.cleaned_data['tariff_coef']))).quantize(TWOPLACES, ROUND_HALF_UP)
            increase = (base * (Decimal(str(form.cleaned_data['increase_percent'])) /
                                Decimal('100'))).quantize(TWOPLACES, ROUND_HALF_UP)
            contract = (base * (Decimal(str(form.cleaned_data['contract_percent'])) /
                                Decimal('100'))).quantize(TWOPLACES, ROUND_HALF_UP)
            total_salary = (base + increase + contract).quantize(TWOPLACES, ROUND_HALF_UP)
            final_salary = (total_salary * (Decimal(str(form.cleaned_data['days_worked'])) /
                                            Decimal(str(form.cleaned_data['schedule_days'])))).quantize(TWOPLACES,
                                                                                                        ROUND_HALF_UP)
            bonus_service = (final_salary * (Decimal(str(form.cleaned_data['percent_experience'])) /
                                             Decimal('100'))).quantize(TWOPLACES, ROUND_HALF_UP)

            # Сохраняем расчеты в модель
            self.object.total_salary = total_salary
            self.object.final_salary = final_salary
            self.object.bonus_service = bonus_service


            self.object.sick_pay = (Decimal(str(form.cleaned_data['daily_rate'])) *
                                    Decimal(str(form.cleaned_data['sick_days']))).quantize(TWOPLACES, ROUND_HALF_UP)
            print(f"Sick pay calculated: {self.object.sick_pay}")

            salary_12_months = self.object.get_salary_12_months()
            average_daily = (Decimal(str(salary_12_months)) / Decimal('29.6')).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.vacation_pay = (average_daily *
                                        Decimal(str(form.cleaned_data['vacation_days']))).quantize(TWOPLACES,
                                                                                                   ROUND_HALF_UP)


            daily_rate = (total_salary / Decimal(str(form.cleaned_data['schedule_days']))).quantize(TWOPLACES,
                                                                                                    ROUND_HALF_UP)
            self.object.maternity_pay = (daily_rate *
                                         Decimal(str(form.cleaned_data['maternity_days']))).quantize(TWOPLACES,
                                                                                                     ROUND_HALF_UP)


            self.object.unpaid_pay = (Decimal(str(form.cleaned_data['daily_rate'])) *
                                      Decimal(str(form.cleaned_data['unpaid_days']))).quantize(TWOPLACES, ROUND_HALF_UP)


            total_accrued = (final_salary + bonus_service + self.object.sick_pay +
                             self.object.vacation_pay + self.object.maternity_pay +
                             Decimal(str(int(form.cleaned_data['bonus']))) +
                             form.cleaned_data['material_assistance'] +
                             form.cleaned_data['health_payment']).quantize(TWOPLACES)

            self.object.tax_deduction = Decimal(str(form.cleaned_data['tax_deduction'])).quantize(TWOPLACES,
                                                                                                  ROUND_HALF_UP)
            taxable_income = (total_accrued - self.object.tax_deduction).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.income_tax = (taxable_income * Decimal('0.13')).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.pension_fund = (total_accrued * Decimal('0.01')).quantize(TWOPLACES, ROUND_HALF_UP)
            self.object.union_fee = (total_accrued * Decimal('0.01')).quantize(TWOPLACES, ROUND_HALF_UP)

            self.object.save()
            print(f"Saved sick pay value: {self.object.sick_pay}")
            return redirect('payroll:salary_report')

        except Exception as e:
            print(f"Error in form_valid: {str(e)}")
            print(f"Form errors: {form.errors}")
            messages.error(self.request, f"Ошибка в расчетах: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("Ошибки формы:", form.errors)
        return super().form_invalid(form)


class SalaryReportView(TemplateView):
    template_name = 'payroll/salary_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_month = self.request.GET.get('month')
        selected_year = self.request.GET.get('year')
        # Изменяем формат отображения года
        years = EmployeeSalary.objects.dates('created_at', 'year')
        years_list = [(year.year, str(year.year)) for year in years]
        # Базовый запрос
        salaries = EmployeeSalary.objects.all()
        if selected_month:
            salaries = salaries.filter(month=selected_month)
        if selected_year:
            salaries = salaries.filter(year=selected_year)
        salaries = salaries.order_by('year', 'month', 'employee__full_name')


        grouped_salaries = {}
        for salary in salaries:
            key = (salary.year, salary.month)
            if key not in grouped_salaries:
                grouped_salaries[key] = []

            total_accrued = (salary.final_salary + salary.bonus_service +
                             salary.sick_pay + salary.vacation_pay +
                             salary.maternity_pay + salary.bonus +
                             salary.material_assistance + salary.health_payment)
            taxable_income = total_accrued - salary.tax_deduction
            income_tax = taxable_income * Decimal('0.13')
            pension_fund = total_accrued * Decimal('0.01')
            union_fee = total_accrued * Decimal('0.01')


            salary.total_accrued = total_accrued
            salary.taxable_income = taxable_income
            salary.income_tax = income_tax
            salary.pension_fund = pension_fund
            salary.union_fee = union_fee
            salary.total_deductions = income_tax + pension_fund + union_fee
            salary.final_payment = total_accrued - (income_tax + pension_fund + union_fee)

            grouped_salaries[key].append(salary)
            print(f"Salary ID: {salary.id}")
            print(f"Sick days: {salary.sick_days}")
            print(f"Sick pay: {salary.sick_pay}")
            print(f"Total accrued: {total_accrued}")
        months = [
            (1, 'Январь'), (2, 'Февраль'), (3, 'Март'),
            (4, 'Апрель'), (5, 'Май'), (6, 'Июнь'),
            (7, 'Июль'), (8, 'Август'), (9, 'Сентябрь'),
            (10, 'Октябрь'), (11, 'Ноябрь'), (12, 'Декабрь')
        ]

        context.update({
            'grouped_salaries': grouped_salaries,
            'months': months,
            'years': years_list,
            'selected_month': selected_month,
            'selected_year': selected_year
        })
        return context
