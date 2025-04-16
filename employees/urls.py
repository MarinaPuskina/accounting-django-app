from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    path('create/', views.EmployeeCreateView.as_view(), name='employee_create'),
]