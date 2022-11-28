from django.urls import path
from medimode.modules.accounts import views

urlpatterns = [
	path('login', views.Login.as_view(), name='login'),
	path('logout', views.Logout.as_view(), name='logout'),
	path('signup/org', views.SignupOrg.as_view(), name='signup_org'),
	path('signup/individual', views.SignupIndividual.as_view(), name='signup_individual'),
	path('signup/doctor', views.SignupDoctor.as_view(), name='signup_doctor'),
	path('profile', views.ProfileView.as_view(), name='profile_details'),
	# path('my_stripe', views.MyStripe.as_view(), name='my_stripe'),
	path('myseed', views.OTPSeed.as_view(), name='seed'),
	path('send_otp', views.SendOTP.as_view(), name='send_otp'),
	path('edit_profile', views.EditProfile.as_view(), name='edit_profile'),
]
