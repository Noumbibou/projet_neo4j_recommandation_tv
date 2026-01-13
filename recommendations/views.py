"""
Views Django avec rendu de templates HTML
Au lieu de retourner du JSON, on retourne des pages HTML
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.models import User as DjangoUser
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import Series, Genre, Actor, Rating, Recommendation
from .decorators import admin_required, get_user_neo4j_id


# ===== PAGES PUBLIQUES =====

def home(request):
    """Page d'accueil"""
    # Récupérer quelques séries populaires
    all_series = Series.get_all()[:8]  # Limiter à 8 séries
    
    context = {
        'series': all_series,
        'page_title': 'Accueil'
    }
    return render(request, 'recommendations/home.html', context)


def _resolve_series(identifier):
    """Résoudre une série à partir d'un series_id OU d'un titre (compat URLs/templates)."""
    if not identifier:
        return None
    serie = Series.get(identifier)
    if serie:
        return serie
    return Series.get_by_title(identifier)


def series_list_view(request):
    """Liste de toutes les séries"""
    series = Series.get_all()
    genres = Genre.get_all()
    
    # Filtrage par genre si demandé
    genre_filter = request.GET.get('genre')
    if genre_filter:
        from tv_recommender.neo4j_db import neo4j_db
        query = """
        MATCH (s:Series)-[:HAS_GENRE]->(g:Genre {name: $genre})
        WHERE s.is_adult = false
        OPTIONAL MATCH (s)-[:HAS_GENRE]->(g2:Genre)
        RETURN s.series_id as series_id,
               s.title as title,
               s.original_title as original_title,
               s.year as year,
               COLLECT(DISTINCT g2.name) as genres
        ORDER BY s.title
        """
        series = neo4j_db.query(query, {'genre': genre_filter})
    
    context = {
        'series': series,
        'genres': genres,
        'selected_genre': genre_filter,
        'page_title': 'Catalogue de séries'
    }
    return render(request, 'recommendations/series_list.html', context)


def series_detail_view(request, title):
    """Détails d'une série"""
    serie = _resolve_series(title)
    
    if not serie:
        messages.error(request, "Série non trouvée")
        return redirect('recommendations:series_list')
    
    # Note moyenne et nombre de notations
    series_id = serie.get('series_id') if serie else None
    rating_info = Rating.get_average_rating(series_id) if series_id else None
    
    # Note de l'utilisateur si connecté
    user_rating = None
    if request.user.is_authenticated:
        user_id = get_user_neo4j_id(request)
        user_rating_data = Rating.get(user_id, series_id) if (user_id and series_id) else None
        if user_rating_data:
            user_rating = user_rating_data.get('rating')
    
    context = {
        'serie': serie,
        'rating_info': rating_info,
        'user_rating': user_rating,
        'page_title': serie['title']
    }
    return render(request, 'recommendations/series_detail.html', context)


def search_view(request):
    """Recherche de séries"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Series.search(query)
    
    context = {
        'query': query,
        'results': results,
        'page_title': f'Recherche: {query}' if query else 'Recherche'
    }
    return render(request, 'recommendations/search.html', context)


# ===== AUTHENTIFICATION =====

def register_view(request):
    """Inscription"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validation
        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas")
        elif DjangoUser.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà")
        elif DjangoUser.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
        else:
            # Créer l'utilisateur
            user = DjangoUser.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            # Connexion automatique
            login(request, user)
            messages.success(request, f"Bienvenue {username} !")
            if user.is_staff:
                return redirect('recommendations:admin_dashboard')
            return redirect('recommendations:home')
    
    return render(request, 'recommendations/register.html', {'page_title': 'Inscription'})


def login_view(request):
    """Connexion"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenue {username} !")
            # Redirection vers la page demandée (si fournie), sinon selon rôle
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('recommendations:admin_dashboard')
            return redirect('recommendations:home')
        else:
            messages.error(request, "Identifiants incorrects")
    
    return render(request, 'recommendations/login.html', {'page_title': 'Connexion'})


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, "Vous êtes déconnecté")
    return redirect('recommendations:home')


# ===== PAGES UTILISATEUR =====

@login_required
def profile_view(request):
    """Profil utilisateur"""
    user_id = get_user_neo4j_id(request)
    # Statistiques
    stats = Rating.get_user_statistics(user_id) if user_id else None
    
    # Notations récentes
    ratings = Rating.get_user_ratings(user_id) if user_id else []
    
    context = {
        'stats': stats,
        'ratings': ratings,
        'page_title': 'Mon Profil'
    }
    return render(request, 'recommendations/profile.html', context)


@login_required
def my_ratings_view(request):
    """Mes notations"""
    user_id = get_user_neo4j_id(request)
    ratings = Rating.get_user_ratings(user_id) if user_id else []
    
    context = {
        'ratings': ratings,
        'page_title': 'Mes Notations'
    }
    return render(request, 'recommendations/my_ratings.html', context)


@login_required
def recommendations_view(request):
    """Recommandations personnalisées"""
    user_id = get_user_neo4j_id(request)
    # Différents types de recommandations
    genre_recs = Recommendation.by_genre(user_id, limit=6) if user_id else []
    collab_recs = Recommendation.collaborative(user_id, limit=6) if user_id else []
    actor_recs = Recommendation.by_actors(user_id, limit=6) if user_id else []
    hybrid_recs = Recommendation.hybrid(user_id, limit=10) if user_id else []
    
    context = {
        'genre_recs': genre_recs,
        'collab_recs': collab_recs,
        'actor_recs': actor_recs,
        'hybrid_recs': hybrid_recs,
        'page_title': 'Recommandations'
    }
    return render(request, 'recommendations/recommendations.html', context)


# ===== AJAX ENDPOINTS POUR LES NOTATIONS =====

@login_required
@require_http_methods(["POST"])
def rate_series_ajax(request):
    """Noter une série (AJAX)"""
    try:
        data = json.loads(request.body)
        series_id = data.get('series_id')
        series_title = data.get('series_title')
        rating_value = int(data.get('score'))
        
        if not (1 <= rating_value <= 5):
            return JsonResponse({'success': False, 'message': 'Score invalide'})

        user_id = get_user_neo4j_id(request)
        serie = Series.get(series_id) if series_id else _resolve_series(series_title)
        resolved_series_id = serie.get('series_id') if serie else None

        if not (user_id and resolved_series_id):
            return JsonResponse({'success': False, 'message': 'Série invalide'})

        Rating.create(user_id, resolved_series_id, rating_value)
        
        # Recalculer la moyenne
        rating_info = Rating.get_average_rating(resolved_series_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Notation enregistrée',
            'average': float(rating_info['average_rating']) if rating_info and rating_info.get('average_rating') is not None else 0,
            'total': rating_info['total_ratings'] if rating_info else 0
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_rating_ajax(request):
    """Supprimer une notation (AJAX)"""
    try:
        data = json.loads(request.body)
        series_id = data.get('series_id')
        series_title = data.get('series_title')

        user_id = get_user_neo4j_id(request)
        serie = Series.get(series_id) if series_id else _resolve_series(series_title)
        resolved_series_id = serie.get('series_id') if serie else None

        if not (user_id and resolved_series_id):
            return JsonResponse({'success': False, 'message': 'Série invalide'})

        deleted = Rating.delete(user_id, resolved_series_id)
        
        if deleted:
            return JsonResponse({'success': True, 'message': 'Notation supprimée'})
        else:
            return JsonResponse({'success': False, 'message': 'Notation non trouvée'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ===== PAGES ADMIN =====

@admin_required
def admin_dashboard_view(request):
    """Dashboard admin"""
    from tv_recommender.neo4j_db import neo4j_db
    
    # Statistiques
    total_users = DjangoUser.objects.count()
    total_series_query = "MATCH (s:Series) RETURN COUNT(s) as count"
    total_series = neo4j_db.query(total_series_query)[0]['count']
    
    # Séries populaires
    popular_query = """
    MATCH (u:User)-[r:RATED]->(s:Series)
    RETURN s.title as title,
           COUNT(r) as ratings_count,
           ROUND(AVG(r.rating) * 10) / 10.0 as avg_rating
    ORDER BY ratings_count DESC
    LIMIT 10
    """
    popular_series = neo4j_db.query(popular_query)
    
    # Utilisateurs actifs
    active_query = """
    MATCH (u:User)-[r:RATED]->(:Series)
    RETURN u.name as username,
           COUNT(r) as ratings_count
    ORDER BY ratings_count DESC
    LIMIT 10
    """
    active_users = neo4j_db.query(active_query)
    
    context = {
        'total_users': total_users,
        'total_series': total_series,
        'popular_series': popular_series,
        'active_users': active_users,
        'page_title': 'Dashboard Admin'
    }
    return render(request, 'recommendations/admin/dashboard.html', context)


@admin_required
def admin_series_list_view(request):
    """Gestion des séries (admin)"""
    series = Series.get_all()
    
    context = {
        'series': series,
        'page_title': 'Gestion des Séries'
    }
    return render(request, 'recommendations/admin/series_list.html', context)


@admin_required
def admin_series_create_view(request):
    """Créer une série (admin)"""
    if request.method == 'POST':
        series_id = request.POST.get('series_id')
        title = request.POST.get('title')
        original_title = request.POST.get('original_title') or title
        year_raw = request.POST.get('year')
        is_adult = (request.POST.get('is_adult') in ('1', 'true', 'True', 'on'))
        
        # Récupérer les genres et acteurs
        genres = request.POST.getlist('genres[]')
        actors = request.POST.getlist('actors[]')

        try:
            if not series_id:
                messages.error(request, "series_id est requis (ex: tt1234567)")
                return redirect('recommendations:admin_series_create')

            year = int(year_raw) if year_raw else None
            
            # Créer la série
            Series.create(series_id, title, original_title, year, is_adult=is_adult)
            
            # Ajouter les genres
            for genre_name in genres:
                if genre_name:
                    Genre.link_to_series(series_id, genre_name.strip())
            
            # Ajouter les acteurs
            for actor_id in actors:
                if actor_id:
                    Actor.link_to_series(series_id, actor_id.strip())
            
            messages.success(request, f"Série '{title}' créée avec succès avec {len(genres)} genre(s) et {len(actors)} acteur(s)")
            return redirect('recommendations:admin_series_list')
        
        except Exception as e:
            messages.error(request, f"Erreur: {e}")
    
    # Récupérer genres et acteurs existants
    all_genres = Genre.get_all()
    all_actors = Actor.get_all(limit=500)  # Limiter pour ne pas surcharger
    
    context = {
        'all_genres': all_genres,
        'all_actors': all_actors,
        'page_title': 'Créer une Série'
    }
    return render(request, 'recommendations/admin/series_form.html', context)

@admin_required
def admin_series_edit_view(request, title):
    """Modifier une série (admin)"""
    serie = _resolve_series(title)
    
    if not serie:
        messages.error(request, "Série non trouvée")
        return redirect('recommendations:admin_series_list')
    
    if request.method == 'POST':
        new_title = request.POST.get('title')
        original_title = request.POST.get('original_title')
        year_raw = request.POST.get('year')
        is_adult = (request.POST.get('is_adult') in ('1', 'true', 'True', 'on'))
        
        # Récupérer les genres et acteurs
        genres = request.POST.getlist('genres[]')
        actors = request.POST.getlist('actors[]')

        try:
            year = int(year_raw) if year_raw else None
            series_id = serie.get('series_id')
            
            # Mettre à jour la série
            Series.update(
                series_id,
                title=new_title,
                original_title=original_title,
                year=year,
                is_adult=is_adult,
            )
            
            # Mettre à jour les genres (supprimer les anciens et ajouter les nouveaux)
            from tv_recommender.neo4j_db import neo4j_db
            
            # Supprimer les anciennes relations de genres
            neo4j_db.query("""
                MATCH (s:Series {series_id: $series_id})-[r:HAS_GENRE]->()
                DELETE r
            """, {'series_id': series_id})
            
            # Ajouter les nouveaux genres
            for genre_name in genres:
                if genre_name:
                    Genre.link_to_series(series_id, genre_name.strip())
            
            # Supprimer les anciennes relations d'acteurs
            neo4j_db.query("""
                MATCH (s:Series {series_id: $series_id})-[r:HAS_ACTOR]->()
                DELETE r
            """, {'series_id': series_id})
            
            # Ajouter les nouveaux acteurs
            for actor_id in actors:
                if actor_id:
                    Actor.link_to_series(series_id, actor_id.strip())
            
            messages.success(request, f"Série '{new_title}' modifiée avec succès")
            return redirect('recommendations:admin_series_list')
        except Exception as e:
            messages.error(request, f"Erreur: {e}")
    
    # Récupérer genres et acteurs existants
    all_genres = Genre.get_all()
    all_actors = Actor.get_all(limit=500)
    
    context = {
        'serie': serie,
        'all_genres': all_genres,
        'all_actors': all_actors,
        'page_title': f'Modifier {title}'
    }
    return render(request, 'recommendations/admin/series_form.html', context)

@admin_required
def admin_series_delete_view(request, title):
    """Supprimer une série (admin)"""
    serie = _resolve_series(title)
    if request.method == 'POST':
        try:
            if not serie:
                messages.error(request, "Série non trouvée")
                return redirect('recommendations:admin_series_list')
            Series.delete(serie.get('series_id'))
            messages.success(request, f"Série '{serie.get('title')}' supprimée")
        except Exception as e:
            messages.error(request, f"Erreur: {e}")
    
    return redirect('recommendations:admin_series_list')


@admin_required
def admin_users_view(request):
    """Gestion des utilisateurs (admin)"""
    users = DjangoUser.objects.all().order_by('-date_joined')
    
    # Ajouter info Neo4j pour chaque user
    users_data = []
    for user in users:
        from .models import User as Neo4jUser
        user_id = str(user.id)
        ratings = Rating.get_user_ratings(user_id)
        users_data.append({
            'user': user,
            'neo4j_exists': Neo4jUser.exists(user_id),
            'ratings_count': len(ratings) if ratings else 0
        })
    
    context = {
        'users_data': users_data,
        'page_title': 'Gestion des Utilisateurs'
    }
    return render(request, 'recommendations/admin/users_list.html', context)

@admin_required
def admin_user_delete_view(request, user_id):
    """Supprimer un utilisateur (admin uniquement)"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(DjangoUser, id=user_id)
            
            # Empêcher la suppression de soi-même
            if user.id == request.user.id:
                messages.error(request, "Vous ne pouvez pas supprimer votre propre compte")
                return redirect('recommendations:admin_users')
            
            # Empêcher la suppression du dernier superuser
            if user.is_superuser:
                superuser_count = DjangoUser.objects.filter(is_superuser=True).count()
                if superuser_count <= 1:
                    messages.error(request, "Impossible de supprimer le dernier superuser")
                    return redirect('recommendations:admin_users')
            
            username = user.username
            user.delete()  # Le signal pre_delete va aussi supprimer de Neo4j
            
            messages.success(request, f"Utilisateur '{username}' supprimé avec succès")
        
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {e}")
    
    return redirect('recommendations:admin_users')


@admin_required
@require_http_methods(["POST"])
def admin_users_delete_multiple_view(request):
    """Supprimer plusieurs utilisateurs (admin uniquement)"""
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({
                'success': False,
                'message': 'Aucun utilisateur sélectionné'
            })
        
        # Vérifier qu'on ne supprime pas l'admin connecté
        current_user_id = str(request.user.id)
        if current_user_id in user_ids:
            return JsonResponse({
                'success': False,
                'message': 'Vous ne pouvez pas supprimer votre propre compte'
            })
        
        # Compter les superusers à supprimer
        users_to_delete = DjangoUser.objects.filter(id__in=user_ids)
        superusers_to_delete = users_to_delete.filter(is_superuser=True).count()
        total_superusers = DjangoUser.objects.filter(is_superuser=True).count()
        
        # Empêcher de supprimer tous les superusers
        if superusers_to_delete > 0 and (total_superusers - superusers_to_delete) < 1:
            return JsonResponse({
                'success': False,
                'message': 'Impossible de supprimer tous les superusers'
            })
        
        # Supprimer les utilisateurs
        deleted_count = 0
        for user in users_to_delete:
            user.delete()  # Le signal va aussi supprimer de Neo4j
            deleted_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} utilisateur(s) supprimé(s) avec succès',
            'deleted_count': deleted_count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })

