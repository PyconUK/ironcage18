from django import forms


class UploadScheduleForm(forms.Form):
    schedule = forms.FileField()


class UploadTimetableForm(forms.Form):
    timetable = forms.FileField()
    unbounded = forms.FileField()
