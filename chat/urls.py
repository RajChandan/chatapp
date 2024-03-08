from django.urls import path
from . import views

urlpatterns = [path('',views.index_view,name='chat-index'),
               path('<srt:room_name>/',views.room_view,name='chat-room')]