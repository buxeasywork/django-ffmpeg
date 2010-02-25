from django.conf import settings
from django.conf.urls.defaults import *
from models import *

urlpatterns = patterns('',
    (r'^convert/', 'vidconvert.views.convert_video'),
    (r'^convert_form/', 'vidconvert.views.convert_video_form'), 
    (r'^get/(?P<id>.*)$','vidconvert.views.get_video'),
    (r'^poster_frame/(?P<id>.*)$','vidconvert.views.poster_frame'),
    (r'^status/(?P<id>.*)$','vidconvert.views.status')
    )