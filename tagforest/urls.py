from django.contrib import admin
from django.urls import include, path

import tags

urlpatterns = [
    path('', include('tags.urls')),
    path('admin/', admin.site.urls),
]
