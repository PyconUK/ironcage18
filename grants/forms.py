from django import forms

from ironcage.widgets import ButtonsCheckbox

from .models import Application


DAY_CHOICES = [
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
]


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'about_you',
            'about_why',
            'requested_ticket_only',
            'amount_requested',
            'cost_breakdown',
        ]

        labels = {
            'about_you': 'Tell us a little bit about yourself',
            'about_why': 'Tell us how you feel attending PyCon UK will be of value',
            'amount_requested': 'What amount in financial assistance would make it possible for you to attend the conference without hardship?',
            'cost_breakdown': 'Please break down the costs you anticipate for travel, accommodation and daily expenses',
        }

        help_texts = {
            'about_you': 'Introduce yourself - tell us about what you do, where you come from and so on. Required.',
            'about_why': 'This can include its value to you, the conference itself, the wider Python community, your own society, or anything at all. Required.',
            'amount_requested': 'Please ensure you specify the currency (preferably in Sterling). Required.',
            'cost_breakdown': 'Please see our <a href="https://2018.pyconuk.org/travel-accommodation" target="_blank">travel and accommodation guidance pages</a> to help calculate your costs. Required.'
        }

        widgets = {
            'about_you': forms.Textarea(attrs={'placeholder': False}),
            'about_why': forms.Textarea(attrs={'placeholder': False}),
            'amount_requested': forms.TextInput(attrs={'placeholder': False}),
            'cost_breakdown': forms.Textarea(attrs={'placeholder': False}),
        }

    requested_ticket_only = forms.ChoiceField(
        choices=Application.REQUESTED_TICKET_ONLY_CHOICES,
        label='Do you need further financial assistance?'
    )

    days = forms.MultipleChoiceField(
        required=True,
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )

    def clean_requested_ticket_only(self):
        # Yes, I know.
        data = self.cleaned_data['requested_ticket_only']
        if data == "True":
            return True
        elif data == "False":
            return False
        return None

    def clean(self):
        cleaned_data = super().clean()

        requested_ticket_only = cleaned_data.get("requested_ticket_only")
        amount_requested = cleaned_data.get("amount_requested")
        cost_breakdown = cleaned_data.get("cost_breakdown")

        if not requested_ticket_only:
            if not amount_requested:
                msg = forms.ValidationError(
                    "Please ensure you provide an amount of assistance you are "
                    "requesting if you require financial assistance outside of "
                    "a free ticket."
                )
                self.add_error('amount_requested', msg)
            if not cost_breakdown:
                msg = forms.ValidationError(
                    "Please ensure you provide a breakdown of the costs you "
                    "anticipate if you require financial assistance outside of "
                    "a free ticket."
                )
                self.add_error('cost_breakdown', msg)
