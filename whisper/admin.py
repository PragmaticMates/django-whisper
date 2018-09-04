from django.contrib import admin
from whisper.models import Room, Message


class MessageInline(admin.StackedInline):
    model = Message
    extra = 1


class MemberInline(admin.TabularInline):
    model = Room.users.through
    verbose_name = "Member"
    verbose_name_plural = "Members"
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    search_fields = ['name', 'slug']
    list_display = ['id', 'name', 'slug', 'created', 'modified']
    inlines = [MemberInline, MessageInline]
