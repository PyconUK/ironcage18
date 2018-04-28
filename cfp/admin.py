from django.contrib import admin
from cfp.models import Proposal
from ironcage.admin import OurActionsOnlyMixin


@admin.register(Proposal)
class ProposalAdmin(OurActionsOnlyMixin, admin.ModelAdmin):
    fields = ('proposer', 'session_type', 'title', 'subtitle',
              'copresenter_names', 'description', 'description_private',
              'outline', 'aimed_at_new_programmers', 'aimed_at_teachers',
              'aimed_at_data_scientists', 'would_like_mentor',
              'would_like_longer_slot', 'state', 'track',
              'special_reply_required', 'scheduled_room', 'scheduled_time')
    readonly_fields = ('proposer', 'session_type', 'title', 'subtitle',
                       'copresenter_names', 'description',
                       'description_private', 'outline',
                       'aimed_at_new_programmers', 'aimed_at_teachers',
                       'aimed_at_data_scientists', 'would_like_mentor',
                       'would_like_longer_slot', 'scheduled_room',
                       'scheduled_time')

    list_display = ('proposer_name', 'session_type', 'title')
    list_filter = ('session_type', )
    search_fields = ['proposer__name', 'title', 'description',
                     'description_private', 'outline']

    def proposer_name(self, obj):
        return obj.proposer.name
