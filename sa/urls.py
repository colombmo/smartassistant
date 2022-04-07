from django.urls import path

from . import views

app_name = "sa"
urlpatterns = [
    path('', views.index, name='index'),
    path('ifttt', views.ifttt, name='ifttt'),
    path('assistant/<str:type>', views.assistant, name='assistant'),
    path('add_ifttt/<str:user_id>', views.add_ifttt, name='add_ifttt'),
    path('execute_query/<str:user_id>/<str:type>', views.execute_query, name="execute_query"),
]