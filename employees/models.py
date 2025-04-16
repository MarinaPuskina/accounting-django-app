from django.db import models


class Employee(models.Model):
    full_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.full_name}"

