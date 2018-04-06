from django import forms
from django.core.exceptions import ValidationError

from ironcage.widgets import ButtonsCheckbox, ButtonsRadio, EmailInput


WHO_CHOICES = [
    ('self', 'Myself'),
    ('others', 'Other people'),
    ('self and others', 'Myself and other people'),
]


RATE_CHOICES = [
    ('individual', 'Individual'),
    ('corporate', 'Corporate'),
    ('education', 'Education'),
]


DAY_CHOICES = [
    ('thu', 'Thursday'),
    ('fri', 'Friday'),
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
]


class TicketForm(forms.Form):
    who = forms.ChoiceField(
        choices=WHO_CHOICES,
        widget=ButtonsRadio
    )
    rate = forms.ChoiceField(
        choices=RATE_CHOICES,
        widget=ButtonsRadio
    )

    @classmethod
    def from_pending_order(cls, order):
        assert order.payment_required()
        unconfirmed_details = order.unconfirmed_details

        data = {
            'rate': unconfirmed_details['rate']
        }

        days_for_self = unconfirmed_details['days_for_self']
        email_addrs_and_days_for_others = unconfirmed_details['email_addrs_and_days_for_others']

        if days_for_self is None:
            assert email_addrs_and_days_for_others is not None
            data['who'] = 'others'
        elif email_addrs_and_days_for_others is None:
            assert days_for_self is not None
            data['who'] = 'self'
        else:
            data['who'] = 'self and others'

        return cls(data)


class TicketForSelfForm(forms.Form):
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )

    @classmethod
    def from_pending_order(cls, order):
        assert order.payment_required()
        unconfirmed_details = order.unconfirmed_details

        days_for_self = unconfirmed_details['days_for_self']
        if days_for_self is None:
            return cls()

        return cls({'days': days_for_self})


class TicketForOtherForm(forms.Form):
    email_addr = forms.EmailField(
        widget=EmailInput(attrs={'class': 'form-control'}),
    )
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )


class BaseTicketForOthersFormset(forms.BaseFormSet):
    def clean(self):
        self.email_addrs_and_days = []
        for form in self.forms:
            if form.errors:
                continue

            if not form.cleaned_data:
                # This was an empty form, so we ignore it
                continue

            email_addr = form.cleaned_data['email_addr']
            days = form.cleaned_data['days']
            self.email_addrs_and_days.append((email_addr, days))

        if not self.email_addrs_and_days:
            raise ValidationError('No valid forms')

    @classmethod
    def from_pending_order(cls, order):
        assert order.payment_required()
        unconfirmed_details = order.unconfirmed_details

        email_addrs_and_days_for_others = unconfirmed_details['email_addrs_and_days_for_others']
        if email_addrs_and_days_for_others is None:
            return cls()

        data = {
            'form-TOTAL_FORMS': str(len(email_addrs_and_days_for_others)),
            'form-INITIAL_FORMS': str(len(email_addrs_and_days_for_others)),
        }

        for ix, (email_addr, days) in enumerate(email_addrs_and_days_for_others):
            data[f'form-{ix}-email_addr'] = email_addr
            data[f'form-{ix}-days'] = days

        return cls(data)


TicketForOthersFormSet = forms.formset_factory(
    TicketForOtherForm,
    formset=BaseTicketForOthersFormset,
    min_num=1,
    extra=1,
    can_delete=True
)


class BillingDetailsForm(forms.Form):
    billing_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    billing_addr = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
