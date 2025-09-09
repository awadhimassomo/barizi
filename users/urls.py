from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


from .views import RegisterView, LoginView, UnifiedLoginView, UserView, login_view, logout_view, register_view, upgrade_account


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('loginapi/', LoginView.as_view(), name='loginapi'),
    path('me/', UserView.as_view(), name='user-info'),
   # path('booking-history/', CustomerBookingHistoryView.as_view(), name='customer-booking-history'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('registerView/', register_view, name='registerView'),
    path('upgrade-account/', upgrade_account, name='upgrade-account'),
    path('api/auth/login/', UnifiedLoginView.as_view(), name='unified-login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   


]
