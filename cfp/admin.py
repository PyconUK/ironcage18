from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from cfp.models import Proposal
from ironcage.admin import OurActionsOnlyMixin


@admin.register(Proposal)
class ProposalAdmin(OurActionsOnlyMixin, admin.ModelAdmin):
    list_filter = ('session_type', 'state', 'replied_to')
    search_fields = ['proposer__name', 'title', 'description',
                     'description_private', 'outline']

    def get_fields(self, request, obj=None):
        users_permissions = request.user.get_all_permissions()

        if (request.user.is_superuser
                or 'cfp.review_education_proposal' in users_permissions   # noqa: W503
                or 'cfp.review_proposal' in users_permissions):  # noqa: W503
            return ['id', 'link_to_proposer', 'session_type', 'title', 'subtitle',
                    'copresenter_names', 'description', 'description_private',
                    'outline', 'aimed_at_new_programmers', 'aimed_at_teachers',
                    'aimed_at_data_scientists', 'would_like_mentor',
                    'would_like_longer_slot', 'state', 'track', 'break_event',
                    'conference_event', 'length_override', 'special_reply_required']

        return ['id', 'session_type', 'title', 'subtitle', 'description']

    def get_readonly_fields(self, request, obj=None):
        fields = self.get_fields(request, obj)

        if request.user.is_superuser:
            fields.remove('title')
            fields.remove('subtitle')
            fields.remove('copresenter_names')
            fields.remove('description')
            fields.remove('track')
            fields.remove('break_event')
            fields.remove('conference_event')
            fields.remove('length_override')

        users_permissions = request.user.get_all_permissions()
        if ('cfp.review_proposal' in users_permissions
                or 'cfp.review_education_proposal' in users_permissions):  # noqa: W503
            if 'aimed_at_new_programmers' in fields:
                fields.remove('aimed_at_new_programmers')
            if 'aimed_at_teachers' in fields:
                fields.remove('aimed_at_teachers')
            if 'aimed_at_data_scientists' in fields:
                fields.remove('aimed_at_data_scientists')
            if 'state' in fields:
                fields.remove('state')

            fields.remove('special_reply_required')

        return fields

    list_display = ('title', 'subtitle', 'proposer_name', 'session_type', 'state')

    def get_search_fields(self, request):
        if request.user.is_superuser:
            return ['proposer__name', 'title', 'subtitle', 'description',
                    'description_private', 'outline']

        return ['title', 'subtitle', 'description']

    def get_queryset(self, request):

        queryset = super().get_queryset(request)

        users_permissions = request.user.get_all_permissions()
        if ('cfp.review_education_proposal' in users_permissions
                and 'cfp.change_proposal' in users_permissions  # noqa: W503
                and 'cfp.review_proposal' not in users_permissions):  # noqa: W503
            return queryset.filter(session_type__in=[
                'kidsworkshop', 'teachersworkshop', 'teacherstalk'
            ])
        else:
            return queryset

    def proposer_name(self, obj):
        return obj.proposer.name

    def link_to_proposer(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.proposer.id])
        return format_html("<a href='{}'>{}</a>", url, obj.proposer.name)
    link_to_proposer.admin_order_field = 'proposer__name'
    link_to_proposer.short_description = 'proposer'

    def response_sent(self, obj):
        return obj.replied_to is not None
