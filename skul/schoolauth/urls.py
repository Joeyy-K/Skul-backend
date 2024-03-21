from django.urls import path
from schoolauth import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('csrf/', views.GetCSRFToken.as_view()),
    path('user/logout/', views.LogoutView.as_view()),
]