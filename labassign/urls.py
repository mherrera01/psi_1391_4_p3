"""labassign URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from core import views

urlpatterns = [
    path('', views.home),
    path('home/', views.home, name='home'),
    path('login/', views.student_login, name='login'),
    path('logout/', views.student_logout, name='logout'),
    path('convalidation/', views.convalidation,
         name='convalidation'),
    path('applypair/', views.applypair, name='applypair'),
    path('breakpair/', views.breakpair, name='breakpair'),
    path('applygroup/', views.applygroup, name='applygroup'),
    path('admin/', admin.site.urls, name='admin'),
    path('groups/', views.groups, name='groups'),
    path('group/<slug:group_name_slug>', views.group, name='group'),
    path('groupchange/', views.groupchange, name='groupchange'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
