from django.urls import path
from .views import SalaryView, SalaryReportView, SalaryEditView


app_name = 'payroll'

urlpatterns = [
    path('salary-edit/<int:pk>/', SalaryEditView.as_view(), name='salary_edit'),
    path('salary-report/', SalaryReportView.as_view(), name='salary_report'),
    path('salary-report/<int:pk>/', SalaryReportView.as_view(), name='salary_detail'),
    path('', SalaryView.as_view(), name='salary_view'),
]