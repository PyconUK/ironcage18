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
    ('unwaged', 'Unwaged'),
]

EDUCATOR_RATE_CHOICES = [
    ('educator-employer', 'Employer funded'),
    ('educator-self', 'Self funded'),
]

DAY_CHOICES = [
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
]

EDUCATOR_DAY_CHOICES = [
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
]


class TicketBaseForm(forms.Form):
    who = forms.ChoiceField(
        choices=WHO_CHOICES,
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

class TicketForm(TicketBaseForm):
    rate = forms.ChoiceField(
        choices=RATE_CHOICES,
        widget=ButtonsRadio
    )

class EducatorTicketForm(TicketBaseForm):
    rate = forms.ChoiceField(
        choices=EDUCATOR_RATE_CHOICES,
        widget=ButtonsRadio
    )


class TicketForSelfBaseForm(forms.Form):

    @classmethod
    def from_pending_order(cls, order):
        assert order.payment_required()
        unconfirmed_details = order.unconfirmed_details

        days_for_self = unconfirmed_details['days_for_self']
        if days_for_self is None:
            return cls()

        return cls({'days': days_for_self})

class TicketForSelfForm(TicketForSelfBaseForm):
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )

class TicketForSelfEducatorForm(TicketForSelfBaseForm):
    days = forms.MultipleChoiceField(
        choices=EDUCATOR_DAY_CHOICES,
        widget=ButtonsCheckbox
    )

class TicketForOtherBaseForm(forms.Form):
    email_addr = forms.EmailField(
        widget=EmailInput(attrs={'class': 'form-control'}),
    )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )


class TicketForOtherForm(TicketForOtherBaseForm):
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )

class TicketForOtherEducatorForm(TicketForOtherBaseForm):
    days = forms.MultipleChoiceField(
        choices=EDUCATOR_DAY_CHOICES,
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

            if form.cleaned_data['DELETE']:
                # This was deleted so should be ignored
                continue

            email_addr = form.cleaned_data['email_addr']
            name = form.cleaned_data['name']
            days = form.cleaned_data['days']
            self.email_addrs_and_days.append((email_addr, name, days))

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

        for ix, (email_addr, name, days) in enumerate(email_addrs_and_days_for_others):
            data[f'form-{ix}-email_addr'] = email_addr
            data[f'form-{ix}-name'] = name
            data[f'form-{ix}-days'] = days

        return cls(data)


TicketForOthersFormSet = forms.formset_factory(
    TicketForOtherForm,
    formset=BaseTicketForOthersFormset,
    min_num=1,
    extra=1,
    can_delete=True
)

TicketForOthersEducatorFormSet = forms.formset_factory(
    TicketForOtherEducatorForm,
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
