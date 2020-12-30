from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


from tambola import views

urlpatterns = [
    path('', views.action_home, name = "action_home"),
    path('login/', views.action_login, name='action_login'),
    path('register/', views.action_register, name='action_register'),
    path('personal_profile/', views.action_personal_prof, name="action_personal_prof"),
    path("logout/", views.action_logout, name = "action_logout"),
    path("photo/<str:username>", views.get_photo, name = "get_photo"),

    # path("refreshroom/<str:room_name>", views.room_serializer, name = "refreshroom"),

    # path('ticket/', views.generate_ticket_json),

    path('room/<str:room_name>/', views.room, name='room'),

    path("click_button", views.click_button, name = "click_button"),

    path('start/<str:room_name>/', views.start_game, name='start_game'),
    
    path('call/<str:room_name>/', views.event_triger_number_drawn, name='event_triger_number_drawn'),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)