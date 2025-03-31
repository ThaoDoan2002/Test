# forms.py
from django import forms
from courses.models import Course


class RevenueFilterForm(forms.Form):
    TIME_CHOICES = [
        ('month', 'Tháng'),
        ('year', 'Năm'),
    ]

    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label="Khóa học")
    time_filter = forms.ChoiceField(choices=TIME_CHOICES, label="Thời gian")
