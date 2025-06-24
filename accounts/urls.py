from django.urls import path
from .views import user_login, user_logout, create_user_view

urlpatterns = [
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('create-user/', create_user_view, name='create_user'),

]