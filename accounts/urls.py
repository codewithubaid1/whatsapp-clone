from django.urls import path
from . import views

urlpatterns =  [
    path('login/',views.login_attempt,name='login'),
    path('regiter',views.register_attempt,name='register'),
    path('verify/<token>',views.verify,name='register'),
    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('reset-password/<token>',views.reset_password,name='reset_password'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('logout/', views.logout_attempt, name='logout'),
]