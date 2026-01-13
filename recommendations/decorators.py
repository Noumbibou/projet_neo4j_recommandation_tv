"""
Décorateurs de permissions adaptés
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect


def admin_required(view_func):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentification requise'
                }, status=401)
            return redirect('recommendations:login')
        
        if not request.user.is_staff:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Permission refusée - Admin uniquement'
                }, status=403)
            return redirect('recommendations:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def get_user_neo4j_id(request):
    """Helper pour obtenir l'user_id Neo4j depuis request.user"""
    if request.user.is_authenticated:
        return str(request.user.id)
    return None
