from django.contrib import admin
from django.urls import include, path

import tags

urlpatterns = [
    path('', include('tags.urls')),
    path('admin/', admin.site.urls),
]

handler404 = 'tags.views.handler404'
handler500 = 'tags.views.handler500'
