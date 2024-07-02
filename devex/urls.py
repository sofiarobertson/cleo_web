from django.urls import path

from devex import views

app_name = "devex"
urlpatterns = [
    path("", views.home, name='home'),
    path("devex/", views.devex, name='devex'),
    path("get-param-value/<str:manager>/<str:param>/", views.get_param_value, name='get_param_value'),
    path("get-param-value/<str:manager>/<str:param>/<str:field>/", views.get_param_value, name='get_param_value_complex'),
    path("get-sampler-value/<str:manager>/<str:sampler>/", views.get_sampler_value, name='get_sampler_value'),
    path("get-sampler-value/<str:manager>/<str:sampler>/<str:field>/", views.get_sampler_value, name='get_sampler_value_complex'),
    path("status/", views.status, name='status'),
    path("get-device/<str:manager>/", views.get_device, name='get_device'),
    path("get-status/<str:manager>/", views.get_status, name='get_status'),
    path("get-state/<str:manager>/", views.get_state, name='get_state'),
]
