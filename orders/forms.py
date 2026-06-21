from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'phone', 'email',
            'address_line_1', 'address_line_2', 'city',
            'state', 'country', 'order_note',
        ]

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        placeholders = {
            'first_name':     'First Name',
            'last_name':      'Last Name',
            'phone':          'Phone Number',
            'email':          'Email Address',
            'address_line_1': 'Address Line 1',
            'address_line_2': 'Address Line 2 (optional)',
            'city':           'City',
            'state':          'State',
            'country':        'Country',
            'order_note':     'Order Note (optional)',
        }
        for field in self.fields:
            self.fields[field].widget.attrs['placeholder'] = placeholders.get(field, '')
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['address_line_2', 'order_note']:
                self.fields[field].required = False