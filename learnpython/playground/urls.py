from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.editcode, name="editcode"),
    path('runcode', views.runcode, name="runcode"),
]
