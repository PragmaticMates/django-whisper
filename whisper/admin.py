from django.contrib import admin
from django.db import models
from django.db.models import Count, Value
from django.db.models.functions import Substr, StrIndex
from django.utils.translation import ugettext_lazy as _
from whisper.models import Room, Message


class MessageInline(admin.StackedInline):
    model = Message
    extra = 1


class MemberInline(admin.TabularInline):
    model = Room.users.through
    verbose_name = _("Member")
    verbose_name_plural = _("Members")
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


class SlugPrefixRoomFilter(admin.SimpleListFilter):
    title = _('slug prefix')
    parameter_name = 'slug_prefix'

    def lookups(self, request, model_admin):
        slug_prefixes = Room.objects.all()\
            .annotate(slug_prefix=Substr('slug', 1, StrIndex('slug',Value('-')) - 1, output_field=models.CharField()))\
            .order_by('slug_prefix')\
            .values_list('slug_prefix', flat=True).distinct()

        lookups = {}

        for prefix in slug_prefixes:
            lookups.update({prefix: _(prefix)})

        return lookups.items()

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(slug__startswith=self.value())


class UsersNumberRoomFilter(admin.SimpleListFilter):
    title = _('number of users')
    parameter_name = 'number_of_users'

    def lookups(self, request, model_admin):
        return (
            ('1', '1 {}'.format(_('user'))),
            ('2', '2 {}'.format(_('users'))),
            ('3', '3 {}'.format(_('and more'))),
        )

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
            lookup = 'gte' if value == 3 else 'exact'
            kwargs = {'count_users__{}'.format(lookup): value}
            qs = queryset.annotate(count_users=Count('users'))
            return qs.filter(**kwargs)
        except (ValueError, TypeError):
            return queryset


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    search_fields = ['name', 'slug']
    list_display = ['id', 'name', 'slug', 'created', 'modified']
    inlines = [MemberInline, MessageInline]
    list_filter = [EmptyRoomFilter, SlugPrefixRoomFilter, UsersNumberRoomFilter]
