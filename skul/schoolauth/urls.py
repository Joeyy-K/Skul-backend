from django.urls import path
from schoolauth import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('csrf/', views.GetCSRFToken.as_view()),
    path('user/logout/', views.LogoutView.as_view()),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)