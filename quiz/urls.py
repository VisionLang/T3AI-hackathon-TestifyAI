from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_quiz, name='generate_quiz'), 
    path('quiz/', views.take_quiz, name='take_quiz'), 
    path('check_quiz/', views.check_quiz, name='check_quiz'), 
]