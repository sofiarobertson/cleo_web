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
    path("script/", views.info, name='script'),
    path("history/<int:pk>/", views.HistoryDetailView.as_view(), name='history_detail'),
    path("recenthistory/<int:pk>/", views.HistoryDetailView2.as_view(), name='history_detailstatus'),
    path("get-antenna/", views.get_antenna, name='get_antenna'),
    path("get-project/", views.get_project, name='get_project'),
    path("antenna/", views.antenna, name='antenna'),
    path("get-antenna-main/", views.get_antenna_main, name='get_antenna_main'),
    path("messages/", views.messages, name='messages'),
    path("get-messages/", views.get_messages, name='get_messages'),
    path("get-messages-main/", views.get_messages_main, name='get_messages_main'),
    path("messages/", views.messages, name='messages'),
    path("get-script/", views.get_script, name='get_script'),
    path("get-script-status/", views.get_script_status, name='get_script_status'),

]
