from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import my_custom_function

urlpatterns = patterns(
    'course_analytics.views',
    url(r"^/$", login_required(my_custom_function), name="django_logic_view")
)