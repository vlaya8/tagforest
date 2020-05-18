from django.urls import path
from . import views

app_name = 'tags'
urlpatterns = [
        path('', views.index, name="index"),
        path('about', views.AboutView.as_view(), name="about"),
        path('tree/<int:tree_id>/view', views.view_tree, name="view_tree")
        path('tree/<int:tree_id>/entry/<int:pk>/', views.DetailEntryView.as_view(), name="detail_entry"),
        path('tree/<int:tree_id>/entry/add', views.add_entry, name="add_entry"),
        path('tree/<int:tree_id>/entry/edit/<int:entry_id>/', views.edit_entry, name="edit_entry"),
        path('tree/<int:tree_id>/entry/process', views.process_entry, name="process_entry"),
        path('tree/<int:tree_id>/entry/delete', views.delete_entry, name="delete_entry"),
        path('tree/<int:tree_id>/tags', views.manage_tags, name="manage_tags"),
]
