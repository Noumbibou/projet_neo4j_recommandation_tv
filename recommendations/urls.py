"""
URLs pour l'application avec templates Django
"""

from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Pages publiques
    path('', views.home, name='home'),
    path('series/', views.series_list_view, name='series_list'),
    path('series/<str:title>/', views.series_detail_view, name='series_detail'),
    path('search/', views.search_view, name='search'),
    
    # Authentification
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Pages utilisateur
    path('profile/', views.profile_view, name='profile'),
    path('my-ratings/', views.my_ratings_view, name='my_ratings'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    
    # AJAX
    path('ajax/rate/', views.rate_series_ajax, name='rate_series_ajax'),
    path('ajax/delete-rating/', views.delete_rating_ajax, name='delete_rating_ajax'),
    
    # Pages admin
    path('backoffice/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('backoffice/series/', views.admin_series_list_view, name='admin_series_list'),
    path('backoffice/series/create/', views.admin_series_create_view, name='admin_series_create'),
    path('backoffice/series/<str:title>/edit/', views.admin_series_edit_view, name='admin_series_edit'),
    path('backoffice/series/<str:title>/delete/', views.admin_series_delete_view, name='admin_series_delete'),
    path('backoffice/users/', views.admin_users_view, name='admin_users'),
    path('backoffice/users/<int:user_id>/delete/', views.admin_user_delete_view, name='admin_user_delete'),
    path('backoffice/users/delete-multiple/', views.admin_users_delete_multiple_view, name='admin_users_delete_multiple'),
]
