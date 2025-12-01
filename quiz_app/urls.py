from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView
app_name = 'quiz_app'
urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('', views.choose_quiz, name='choose_quiz'),
    path('start/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:attempt_id>/', views.quiz_page, name='quiz_page'),
    path('submit/<int:attempt_id>/', views.submit_quiz, name='submit_quiz'),
    path('result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('history/', views.history_view, name='history'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
