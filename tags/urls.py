from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tags'
urlpatterns = [
        path('', views.index, name="index"),

        path('tree/<int:tree_id>/view/', views.view_tree, name="view_tree"),

        path('tree/<int:tree_id>/entry/<int:entry_id>/', views.detail_entry, name="detail_entry"),
        path('tree/<int:tree_id>/entry/add/', views.add_entry, name="add_entry"),
        path('tree/<int:tree_id>/entry/edit/<int:entry_id>/', views.edit_entry, name="edit_entry"),
        path('tree/<int:tree_id>/entry/process/', views.process_entry, name="process_entry"),
        path('tree/<int:tree_id>/entry/delete/', views.delete_entry, name="delete_entry"),

        path('tree/process', views.process_tree, name="process_tree"),

        path('tree/<int:tree_id>/tags/', views.manage_tags, name="manage_tags"),
        path('manage_tags/', views.manage_tags_default, name="manage_tags_default"),

        path('accounts/login/', auth_views.LoginView.as_view(template_name='tags/registration/login.html')),
        path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='tags/registration/password_change_form.html')),

        path('accounts/profile/', views.ProfileView.as_view(), name="profile"),
        path('accounts/signup/', views.signup, name="signup"),
        path('accounts/', include('django.contrib.auth.urls')),

        path('about/', views.AboutView.as_view(), name="about"),
]
