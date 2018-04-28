class OurActionsOnlyMixin():

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def change_view(self, request, object_id=None, form_url='',
                    extra_context=None):
        # Hide save button if all fields are readonly
        fields = self.get_fields(request)
        readonly_fields = self.get_readonly_fields(request)

        if set(fields).issubset(readonly_fields):
            extra_context = extra_context or {}
            extra_context['show_save_and_continue'] = False
            extra_context['show_save'] = False

        return super().change_view(request, object_id,
                                   extra_context=extra_context)
