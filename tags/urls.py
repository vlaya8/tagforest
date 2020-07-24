from django.urls import path, include, reverse
from django.contrib.auth import views as auth_views
from . import views
from .views import SpecialID

app_name = 'tags'

tree_urlpatterns = [
    path('', views.ViewTreeView.as_view(), name="view_tree"),
    path('tree/', include([
        path('', views.ViewTreeView.as_view(), name="view_tree"),
        path('<int:tree_id>/', include([
            path('view/', views.ViewTreeView.as_view(), name="view_tree"),
            path('entry/', include([
                path('', views.ViewEntryView.as_view(), name="view_entry"),
                path('<int:entry_id>/view/', views.ViewEntryView.as_view(), name="view_entry"),
                path('add/', views.UpsertEntryView.as_view(), name="upsert_entry"),
                path('<int:entry_id>/edit/', views.UpsertEntryView.as_view(), name="upsert_entry"),
            ])),
        ])),
    ])),
]

login_view = auth_views.LoginView.as_view(
                                template_name='tags/registration/login.html',
                                extra_context={'current_page': 'login'},
)

urlpatterns = [
        path('', views.index, name="index"),
        path('group/<str:group_name>/', include(tree_urlpatterns)),
        path('user/<str:username>/', include([
            path('profile/', views.ProfileView.as_view(), name="profile"),
        ])),
        path('notifications/', views.ViewNotificationsView.as_view(), name="view_notifications"),
        path('notification/<int:notification_id>/', views.ViewNotificationView.as_view(), name="view_notification"),
        path('groups/', include([
            path('', views.ViewGroupsView.as_view(), name="view_groups"),
            path('group/', include([
                path('', views.ViewGroupView.as_view(), name="view_group"),
                path('<int:group_id>/view/', views.ViewGroupView.as_view(), name="view_group"),
                path('add/', views.UpsertGroupView.as_view(), name="upsert_group"),
                path('<int:group_id>/edit/', views.UpsertGroupView.as_view(), name="upsert_group"),
            ])),
        ])),
        path('about/', views.AboutView.as_view(), name="about"),
        path('post_login/', views.post_login, name="post_login"),
        path('accounts/', include([
            path('password_change/', views.ChangePasswordView.as_view()),
            path('login/', login_view),
            path('signup/', views.SignupView.as_view(), name="signup"),
            path('signup/success', views.SignupSuccessView.as_view(), name="signup_success"),
            path('', include('django.contrib.auth.urls')),
        ])),
]

