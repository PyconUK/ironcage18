from django import forms
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from .models import ChildrenTicket


class ChildrenTicketForm(forms.ModelForm):
    class Meta:
        model = ChildrenTicket
        fields = [
            'adult_name',
            'adult_email_addr',
            'adult_phone_number',
            'name',
            'age',
            'accessibility_reqs',
            'dietary_reqs',
        ]

        labels = {
            'adult_name': "Adult's Name",
            'adult_email_addr': "Adult's Email Address",
            'adult_phone_number': "Adult's Phone Number",
            'name': "Child's First Name",
            'age': "Child's Age",
            'accessibility_reqs': "Accessibility Requirements",
            'dietary_reqs': "Dietary Requirements",
        }

        help_texts = {
            'adult_name': 'Name of the supervising adult',
            'adult_email_addr': 'E-mail address of the supervising adult',
            'adult_phone_number': 'Phone number of the supervising adult',
            'name': 'First name of the child',
            'age': 'Age of the child on 15th September 2018',
            'accessibility_reqs': 'Any accessibility requirements for the child or supervising adult',
            'dietary_reqs': 'Any dietary requirements for the child or supervising adult',
        }

        widgets = {
            'adult_name': forms.TextInput(attrs={'placeholder': False}),
            'adult_phone_number': forms.TextInput(attrs={'placeholder': False}),
            'adult_email_addr': forms.EmailInput(attrs={'placeholder': False}),
            'name': forms.TextInput(attrs={'placeholder': False}),
            'age': forms.NumberInput(attrs={'placeholder': False}),
            'accessibility_reqs': forms.Textarea(attrs={'placeholder': False}),
            'dietary_reqs': forms.Textarea(attrs={'placeholder': False}),
        }

    @classmethod
    def from_pending_order(cls, order):
        assert order.payment_required()
        unconfirmed_details = order.unconfirmed_details

        data = {
            'adult_name': unconfirmed_details['adult_name'],
            'adult_email_addr': unconfirmed_details['adult_email_addr'],
            'adult_phone_number': unconfirmed_details['adult_phone_number'],
            'name': unconfirmed_details['name'],
            'age': unconfirmed_details['age'],
            'accessibility_reqs': unconfirmed_details['accessibility_reqs'],
            'dietary_reqs': unconfirmed_details['dietary_reqs'],
        }

        return cls(data)
