from django.conf.urls.defaults import patterns
import views

urlpatterns = patterns('',
    # Dummy index view
    (r'^$', views.index),
)
