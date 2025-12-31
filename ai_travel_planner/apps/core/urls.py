from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'apps.core'

urlpatterns = [
    path('', TemplateView.as_view(template_name='core/home.html'), name='home'),
    path('about/', TemplateView.as_view(template_name='core/about.html'), name='about'),
    path('how-it-works/', TemplateView.as_view(template_name='core/how_it_works.html'), name='how_it_works'),
    path("faq/", views.faq_view, name="faq"),
    path("terms/", views.terms_view, name="terms"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("contact/", views.contact_view, name="contact"),
]