from django.urls import path

from devex import views

app_name = "devex"
urlpatterns = [
    path("", views.devex, name='devex'),
    path("get-param-value/<str:manager>/<str:param>/", views.get_param_value, name='get_param_value'),
    path("get-param-value/<str:manager>/<str:param>/<str:field>/", views.get_param_value, name='get_param_value_complex'),
]
