from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.codeedit, name="codeedit"),
    path('runcode', views.runcode, name="runcode"),
]
