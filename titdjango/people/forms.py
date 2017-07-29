from django import forms

class PeopleForm(forms.Form):
    phone = forms.CharField(max_length=11,min_length=11)
    email = forms.CharField(max_length=255)
