from django import forms

from .models import (CITY_HALL_DESSERTS, CITY_HALL_DINNERS, CITY_HALL_MAINS,
                     CITY_HALL_STARTERS, CLINK_DESSERTS, CLINK_DINNERS,
                     CLINK_MAINS, CLINK_STARTERS, ChildrenTicket, DinnerTicket)


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


class DinnerTicketForm(forms.ModelForm):

    class Meta:
        model = DinnerTicket
        fields = [
            'dinner',
            'starter',
            'main',
            'dessert',
        ]

    @classmethod
    def from_pending_order(cls, order):
        assert order.payment_required()
        unconfirmed_details = order.unconfirmed_details

        data = {
            'dinner': unconfirmed_details['dinner'],
            'starter': unconfirmed_details['starter'],
            'main': unconfirmed_details['main'],
            'dessert': unconfirmed_details['dessert'],
        }

        if data['dinner'] in ['CD']:
            return CityHallDinnerTicketForm(data)
        else:
            return ClinkDinnerTicketForm(data)

    @classmethod
    def from_item(cls, item):
        assert not item.order.payment_required()

        data = {
            'dinner': item.item.dinner,
            'starter': item.item.starter,
            'main': item.item.main,
            'dessert': item.item.dessert,
        }

        if item.item.dinner in ['CD']:
            return CityHallDinnerTicketForm(data)
        else:
            return ClinkDinnerTicketForm(data)


class ClinkDinnerTicketForm(DinnerTicketForm):
    dinner = forms.ChoiceField(label='Event', choices=CLINK_DINNERS)
    starter = forms.ChoiceField(choices=CLINK_STARTERS)
    main = forms.ChoiceField(label='Main Course', help_text='gf: Gluten Free, v: vegetarian, vg: vegan', choices=CLINK_MAINS)
    dessert = forms.ChoiceField(choices=CLINK_DESSERTS)


class CityHallDinnerTicketForm(DinnerTicketForm):
    dinner = forms.ChoiceField(label='Event', choices=CITY_HALL_DINNERS)
    starter = forms.ChoiceField(choices=CITY_HALL_STARTERS)
    main = forms.ChoiceField(label='Main Course', help_text='gf: Gluten Free, v: vegetarian, vg: vegan', choices=CITY_HALL_MAINS)
    dessert = forms.ChoiceField(choices=CITY_HALL_DESSERTS)
