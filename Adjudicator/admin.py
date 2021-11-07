from django.contrib import admin
from Adjudicator.models import *
from django.contrib.auth.admin import Group


class TeamAdmin(admin.ModelAdmin):
    list_display = ('login', 'name', 'image', 'network_address')
    list_editable = ('name', 'image', 'network_address')


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'network_address', 'network_port')
    list_editable = ('name', 'network_address', 'network_port')


class RoundAdmin(admin.ModelAdmin):
    #actions = None
    list_display = ('number', 'status', 'begin_time', 'end_time')
    list_editable = ('end_time',)
    """
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def __init__(self, *args, **kwargs):
        super(RoundAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )
    """

class FlagAdmin(admin.ModelAdmin):
    #actions = None
    list_display = ('round', 'service', 'team', 'flag')
    list_filter = ('service', 'team', 'round')
    search_fields = ('flag', )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def __init__(self, *args, **kwargs):
        super(FlagAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )


class AdvisoryAdmin(admin.ModelAdmin):
    list_display = ('team', 'service', 'datetime', 'is_visible', 'points')
    list_filter = ('is_visible', 'team')
    list_editable = ('points', 'is_visible')


class ScoreAdmin(admin.ModelAdmin):
    list_display = ('round', 'team', 'service', 'service_points', 'status', 'comment')
    list_filter = ('service', 'team', 'round', 'status')


class MainParamsAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'started', 'ended')
    list_editable = ('start_time', 'end_time', 'started', 'ended')
    actions = None

    def __init__(self, *args, **kwargs):
        super(MainParamsAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def has_delete_permission(self, request, obj=None):
        return False


class NewsAdmin(admin.ModelAdmin):
    list_display = ('caption', 'author', 'datetime')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('caption', 'nickname', 'team', 'new', 'datetime')
    list_filter = ('team',)


class LogAdmin(admin.ModelAdmin):
    #actions = None
    list_display = ('team', 'round', 'flag', 'datetime', 'status')
    list_filter = ('team', 'round', 'status')
    """
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    """

admin.site.unregister(Group)
admin.site.register(Team, TeamAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Flag, FlagAdmin)
admin.site.register(Advisory, AdvisoryAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(MainParams, MainParamsAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Log, LogAdmin)