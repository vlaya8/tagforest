from django.urls import path
from . import views

app_name = 'tags'
urlpatterns = [
        path('', views.index, name="index"),
        path('about', views.AboutView.as_view(), name="about"),
        path('entry/<int:pk>/', views.DetailEntryView.as_view(), name="detail_entry"),
        path('entry/add', views.add_entry, name="add_entry"),
        path('entry/edit/<int:entry_id>/', views.edit_entry, name="edit_entry"),
        path('entry/process', views.process_entry, name="process_entry"),
        path('entry/delete', views.delete_entry, name="delete_entry"),
        path('tags', views.manage_tags, name="manage_tags"),
]
