# coding=utf-8
from django.conf.urls import patterns, include, url
from django.contrib import admin
from Adjudicator import views, utils

admin.autodiscover()

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'FinalSystem.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),

                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^$', views.main_view, name='TestPage'),
                       url(r'^news/(?P<new_id>\d+)/$', views.one_new_view, name='OneNew'),
                       url(r'^news/$', views.all_news_view, name='News'),
                       url(r'^advisory/$', views.advisory_view, name='Advisories'),
                       url(r'^scoreboard/(?P<one_round_number>\d+)/$', views.scoreboard_view, name='Scoreboard'),
                       url(r'^scoreboard/', views.scoreboard_view, name='Scoreboard'),
                       url(r'^flag/$', views.check_flag_view, name='CheckFlag'),
                       url(r'^check_new_round/$', views.check_view),
)


from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

#only for debug!!!
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()