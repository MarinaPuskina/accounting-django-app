from django.views.generic import ListView, CreateView
from .models import Employee
from .forms import EmployeeForm


class EmployeeListView(ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for employee in context['employees']:
            employee.hire_date = employee.hire_date.strftime('%d.%m.%Y')
        return context


class EmployeeCreateView(CreateView):
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = '/employees/'

    def form_valid(self, form):
        print("Form data:", form.cleaned_data)
        response = super().form_valid(form)
        self.object = form.save()
        return response




# Create your views here.
