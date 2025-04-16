from django.db import models
from decimal import Decimal
from employees.models import Employee
from datetime import datetime, timedelta
from django.db.models import Sum


class EmployeeSalary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    rate_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tariff_coef = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    increase_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    contract_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    percent_experience = models.IntegerField(default=0)
    days_worked = models.IntegerField(default=0)
    schedule_days = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    sick_days = models.IntegerField(default=0)
    vacation_days = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    maternity_days = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    unpaid_days = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.IntegerField(
        verbose_name='Премия',
        default=0
    )
    material_assistance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    health_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Налогооблагаемая база'
    )


    # Поля для расчетов
    total_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus_service = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sick_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vacation_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maternity_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unpaid_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # Поля для удержаний
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pension_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    union_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    class Meta:
        ordering = ['-created_at']
        db_table = 'payroll_employeesalary'

    def get_salary_12_months(self):
        end_date = datetime(self.year, self.month, 1)
        start_date = end_date - timedelta(days=365)

        salaries = EmployeeSalary.objects.filter(
            employee=self.employee,
            year__gte=start_date.year,
            month__gte=start_date.month,
            year__lte=end_date.year,
            month__lte=end_date.month
        ).exclude(id=self.id)

        total_salary = salaries.aggregate(
            total=Sum('final_salary') +
                  Sum('bonus_service')
            # Исключаем больничные, материальную помощь, премии и прочие выплаты
        )['total'] or 0

        return Decimal(str(total_salary))

# Create your models here.
