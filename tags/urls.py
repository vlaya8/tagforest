from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tags'

user_urlpatterns = [
    path('tree/<int:tree_id>/', include([
        path('view/', views.view_tree, name="view_tree"),
        path('tags/', views.manage_tags, name="manage_tags"),
        path('entry/', include([
            path('<int:entry_id>/', views.detail_entry, name="detail_entry"),
            path('add/', views.add_entry, name="add_entry"),
            path('edit/<int:entry_id>/', views.edit_entry, name="edit_entry"),
            path('process/', views.process_entry, name="process_entry"),
            path('delete/', views.delete_entry, name="delete_entry"),
        ])),
    ])),
    path('tree/process', views.process_tree, name="process_tree"),
    path('manage_tags/', views.manage_tags_default, name="manage_tags_default"),
]

urlpatterns = [
        path('', views.index, name="index"),
        path('<str:username>/', include(user_urlpatterns)),
        path('about/', views.AboutView.as_view(), name="about"),
        path('accounts/', include([
            path('login/', auth_views.LoginView.as_view(template_name='tags/registration/login.html')),
            path('password_change/', auth_views.PasswordChangeView.as_view(template_name='tags/registration/password_change_form.html')),
            path('profile/', views.ProfileView.as_view(), name="profile"),
            path('signup/', views.signup, name="signup"),
            path('', include('django.contrib.auth.urls')),
        ])),
]
