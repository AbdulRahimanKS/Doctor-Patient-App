from django.urls import path
from accounts.views import IndexView, LandingPageView, SignupView, SignInView, SignOutView


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('landing_page/', LandingPageView.as_view(), name='landing_page'),   
    path('sign_up/', SignupView.as_view(), name='sign_up'),
    path('sign_in/', SignInView.as_view(), name='sign_in'),
    path('sign_out/', SignOutView.as_view(), name='sign_out')
]

