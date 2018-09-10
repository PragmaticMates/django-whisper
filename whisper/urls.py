from django.urls import path
from django.utils.translation import pgettext_lazy

from whisper.views import RoomView, RoomUpdateView, RoomLeaveView, RoomAddMemberView, RoomListView

app_name = 'whisper'

urlpatterns = [
    path(pgettext_lazy('url', 'room/<slug>/update/'), RoomUpdateView.as_view(), name='room_update'),
    path(pgettext_lazy('url', 'room/<slug>/leave/'), RoomLeaveView.as_view(), name='room_leave'),
    path(pgettext_lazy('url', 'room/<slug>/add-member/'), RoomAddMemberView.as_view(), name='room_add_member'),
    path(pgettext_lazy('url', 'room/<slug>/'), RoomView.as_view(), name='room_detail'),
    path(pgettext_lazy('url', 'room/'), RoomListView.as_view(), name='room_list'),
]
