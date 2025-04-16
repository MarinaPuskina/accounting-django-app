from django.views.generic import CreateView
from .models import EmployeeSalary
from employees.models import Employee
from django import forms
from django.contrib import messages
from decimal import Decimal
from datetime import datetime
from django.shortcuts import redirect


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
    percent_experience = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Процент за стаж'
    )
    bonus = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0'
        }),
        label='Премия',
        initial=0
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
        label='Дневная ставка'
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
        label='Выплата на оздоровление',
        initial=0
    )
    tax_deduction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Налоговый вычет',
        initial=0
    )

    class Meta:
        model = EmployeeSalary
        fields = [
            'employee', 'month', 'year', 'rate_1', 'tariff_coef',
            'increase_percent', 'contract_percent', 'percent_experience',
            'days_worked', 'schedule_days', 'sick_days', 'vacation_days',
            'maternity_days', 'unpaid_days', 'daily_rate', 'bonus',
            'material_assistance', 'health_payment', 'tax_deduction'
        ]


class SalaryView(CreateView):
    model = EmployeeSalary
    form_class = TimeSheetForm
    template_name = 'payroll/salary_view.html'
    TWOPLACES = Decimal('0.01')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            # Расчеты базового оклада
            base = (Decimal(str(form.cleaned_data['rate_1'])) *
                    Decimal(str(form.cleaned_data['tariff_coef']))).quantize(TWOPLACES)
            increase = (base * (Decimal(str(form.cleaned_data['increase_percent'])) /
                                Decimal('100'))).quantize(TWOPLACES)
            contract = (base * (Decimal(str(form.cleaned_data['contract_percent'])) /
                                Decimal('100'))).quantize(TWOPLACES)
            total_salary = (base + increase + contract).quantize(TWOPLACES)

            final_salary = (total_salary * (Decimal(str(form.cleaned_data['days_worked'])) /
                                            Decimal(str(form.cleaned_data['schedule_days'])))).quantize(TWOPLACES)
            bonus_service = (final_salary * (Decimal(str(form.cleaned_data['percent_experience'])) /
                                             Decimal('100'))).quantize(TWOPLACES)

            # Сохраняем расчеты в модель
            self.object.total_salary = total_salary
            self.object.final_salary = final_salary
            self.object.bonus_service = bonus_service

            # Расчет дополнительных выплат
            self.object.sick_pay = Decimal(str(form.cleaned_data['daily_rate'])) * Decimal(
                str(form.cleaned_data['sick_days']))
            self.object.vacation_pay = Decimal(str(form.cleaned_data['daily_rate'])) * Decimal(
                str(form.cleaned_data['vacation_days']))
            self.object.maternity_pay = Decimal(str(form.cleaned_data['daily_rate'])) * Decimal(
                str(form.cleaned_data['maternity_days']))

            # Расчет удержаний
            total_accrued = (final_salary + bonus_service + self.object.sick_pay +
                             self.object.vacation_pay + self.object.maternity_pay +
                             form.cleaned_data['bonus'] + form.cleaned_data['material_assistance'] +
                             form.cleaned_data['health_payment']).quantize(TWOPLACES)

            self.object.income_tax = total_accrued * Decimal('0.13')
            self.object.pension_fund = total_accrued * Decimal('0.01')
            self.object.union_fee = total_accrued * Decimal('0.01')

            self.object.save()
            return redirect('payroll:accrued', pk=self.object.pk)

        except Exception as e:
            messages.error(self.request, f"Ошибка в расчетах: {str(e)}")
            return self.form_invalid(form)
