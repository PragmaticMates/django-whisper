from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from whisper.models import Room, Message


class MessageInline(admin.StackedInline):
    model = Message
    extra = 1


class MemberInline(admin.TabularInline):
    model = Room.users.through
    verbose_name = "Member"
    verbose_name_plural = "Members"
    extra = 1


class EmptyRoomFilter(admin.SimpleListFilter):
    title = _('empty')
    parameter_name = 'empty'

    def lookups(self, request, model_admin):
        return (
            ('no', _('no')),
            ('yes', _('yes')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.not_empty()
        if self.value() == 'yes':
            return queryset.empty()


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    search_fields = ['name', 'slug']
    list_display = ['id', 'name', 'slug', 'created', 'modified']
    inlines = [MemberInline, MessageInline]
    list_filter = [EmptyRoomFilter]
