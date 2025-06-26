from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout_view, name='logout'),
    
    # User management endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('current-user/', views.current_user_view, name='current_user'),
    
    # Admin endpoints
    path('link-lawyer/', views.LinkLawyerProfileView.as_view(), name='link_lawyer'),
]