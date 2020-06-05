from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tags'

user_urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name="profile"),
    path('tree/<int:tree_id>/', include([
        path('view/', views.ViewTreeView.as_view(), name="view_tree"),
        path('tags/', views.ManageTagsView.as_view(), name="manage_tags"),
        path('entry/', include([
            path('<int:entry_id>/', views.ViewEntryView.as_view(), name="view_entry"),
            path('add/', views.UpsertEntryView.as_view(), name="upsert_entry"),
            path('<int:entry_id>/edit/', views.UpsertEntryView.as_view(), name="upsert_entry"),
        ])),
    ])),
]

urlpatterns = [
        path('', views.index, name="index"),
        path('<str:username>/', include(user_urlpatterns)),
        path('about/', views.AboutView.as_view(), name="about"),
        path('accounts/', include([
            path('login/', auth_views.LoginView.as_view(template_name='tags/registration/login.html')),
            path('password_change/', auth_views.PasswordChangeView.as_view(template_name='tags/registration/password_change.html')),
            path('signup/', views.signup, name="signup"),
            path('', include('django.contrib.auth.urls')),
        ])),
]
