from whisper import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.module_loading import import_string
from django.views.generic import DetailView, UpdateView, ListView
from whisper.models import Room, RoomUser


class RoomView(LoginRequiredMixin, DetailView):
    model = Room


class RoomListView(LoginRequiredMixin, ListView):
    model = Room

    def get_queryset(self):
        return super().get_queryset().recent(self.request.user)


class RoomLeaveView(LoginRequiredMixin, DetailView):
    model = Room

    def dispatch(self, request, *args, **kwargs):
        room = self.get_object()
        user = request.user
        RoomUser.objects.filter(user=user, room=room).delete()
        return redirect('/')


class RoomUpdateView(LoginRequiredMixin, UpdateView):
    model = Room
    fields = ['name']

    def get_form_class(self):
        form_class = settings.ROOM_FORM_CLASS
        return import_string(form_class) if form_class else super().get_form_class()


class RoomAddMemberView(LoginRequiredMixin, UpdateView):
    model = Room
    fields = ['users']
    template_name = 'whisper/add_member_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'current_user': self.user})
        return kwargs

    @staticmethod
    def load_form_class():
        form_class = settings.ROOM_ADD_MEMBER_FORM_CLASS

        if form_class:
            form_class = import_string(form_class)

        return form_class

    def get_form_class(self):
        return self.load_form_class()
