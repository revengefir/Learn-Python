from django.urls import path
from .views import codeedit, runcode

urlpatterns = [
    path("", codeedit, name="playground"),
    path("run", runcode, name="run"),
]
