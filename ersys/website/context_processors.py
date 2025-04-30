def admin_session(request):
    """Make admin session data available to all templates."""
    return {
        'is_impersonating': 'original_admin_id' in request.session,
        'original_admin_id': request.session.get('original_admin_id', None),
    }