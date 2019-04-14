from django.conf.urls import url
from . import views


urlpatterns = [

    # User Authentication
    url('^login/$', views.UserLoginView.as_view(), name='login'),
    url('^logout/$', views.UserLogoutView.as_view(), name='logout'),

    # user Creation
    url(r'^signup/$', views.UserCreateView.as_view(), name='create-user'),

    # user mail verification
    url(r'^mail_verify/(?P<id>\w+)/$', views.MailVerificationView, name='mail-verify'),

    # resend (all kind of mailverifications)
    url(r'^resend/$', views.send.as_view(), name='resend'),

    # users ListView
    url(r'^users/$', views.UserListView.as_view(), name='user-list'),


    # update user
    url(r'^update/(?P<pk>\d+)/$', views.UserUpdateView.as_view(), name='user-update'),
    url(r'^email_verify/(?P<id>\w+)/$', views.EmailChangeVerifyView.as_view(), name='email-verify'),

    # user forgot password operation.
    url(r'^forgot_password_update/(?P<id>\w+)/$', views.ForgotUserPasswordUpdateView.as_view(), name='forgot-password'),
    url(r'^forgot_password/', views.password_forgot, name='forgot_update'),

    # update user password
    url(r'^password_update/$', views.UserPasswordUpdateView.as_view(), name='password-update'),

    # Mobile Verification Views
    url(r'^mobile-verify/$', views.MobileVerifyView.as_view()),
    url(r'^mobile-resend/$', views.ResendMobileVerify.as_view()),

    # AdminLinkGenerate and Register urls
    url(r'^admin-link/$', views.GenerateAdminLink.as_view()),
    url(r'^validate/adminlink/$', views.ValidateAdminLink.as_view()),
    url(r'^admin-register/(?P<link>\w+)/$', views.AdminCreateView.as_view()),

    # Disable/Enable User
    url(r'^update/access/(?P<pk>\d+)/$', views.DisableUser.as_view())
]