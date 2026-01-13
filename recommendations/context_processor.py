"""
Context processor pour ajouter des variables globales aux templates
"""

def user_neo4j_context(request):
    """Ajouter l'user_id Neo4j au contexte de tous les templates"""
    context = {}
    
    if request.user.is_authenticated:
        context['user_neo4j_id'] = str(request.user.id)
        
        # Ajouter les stats utilisateur si besoin
        from recommendations.models import Rating
        try:
            stats = Rating.get_user_statistics(str(request.user.id))
            context['user_stats'] = stats
        except:
            context['user_stats'] = None
    
    return context