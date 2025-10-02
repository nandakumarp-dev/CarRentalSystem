from django.conf import settings

def site_settings(request):
    """Add site-wide settings to template context"""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'DriveRental'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', 'Your trusted car rental platform'),
        'SUPPORT_EMAIL': getattr(settings, 'SUPPORT_EMAIL', 'support@driverental.com'),
        'SUPPORT_PHONE': getattr(settings, 'SUPPORT_PHONE', '+1-555-123-4567'),
        'COMPANY_ADDRESS': getattr(settings, 'COMPANY_ADDRESS', '123 Rental Street, City, State 12345'),
    }

def user_context(request):
    """Add user-related context"""
    context = {}
    if request.user.is_authenticated:
        context['user_profile'] = getattr(request.user, 'customer_profile', None) or getattr(request.user, 'owner_profile', None)
    return context