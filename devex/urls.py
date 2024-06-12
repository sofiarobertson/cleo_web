from django.urls import path

from devex import views

app_name = "devex"
urlpatterns = [
    path("", views.devex, name='devex')
]
