from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .forms import UserRegistrationForm, UserProfileForm
from apps.trips.models import TripRequest, Itinerary


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('core:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    """User profile view and edit"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user statistics
    stats = {
        'total_trips': TripRequest.objects.filter(user=request.user).count(),
        'completed_trips': TripRequest.objects.filter(user=request.user, status='completed').count(),
        'processing_trips': TripRequest.objects.filter(user=request.user, status='processing').count(),
        'favorite_itineraries': Itinerary.objects.filter(trip_request__user=request.user, is_favorite=True).count(),
    }
    
    context = {
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def dashboard(request):
    """User dashboard with statistics and recent trips"""
    
    # Get recent trips
    recent_trips = TripRequest.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get favorite itineraries
    favorite_itineraries = Itinerary.objects.filter(
        trip_request__user=request.user,
        is_favorite=True
    ).select_related('trip_request')[:5]
    
    # Calculate statistics
    total_trips = TripRequest.objects.filter(user=request.user).count()
    completed_trips = TripRequest.objects.filter(user=request.user, status='completed').count()
    processing_trips = TripRequest.objects.filter(user=request.user, status='processing').count()
    failed_trips = TripRequest.objects.filter(user=request.user, status='failed').count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_activity = TripRequest.objects.filter(
        user=request.user,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Most visited destinations
    top_destinations = TripRequest.objects.filter(
        user=request.user,
        status='completed'
    ).values('destination').annotate(
        count=Count('destination')
    ).order_by('-count')[:5]
    
    # Travel style preferences
    travel_styles = TripRequest.objects.filter(
        user=request.user
    ).values('travel_style').annotate(
        count=Count('travel_style')
    ).order_by('-count')[:3]
    
    # Total budget spent (completed trips)
    from django.db.models import Sum
    total_budget = TripRequest.objects.filter(
        user=request.user,
        status='completed'
    ).aggregate(total=Sum('budget'))['total'] or 0
    
    context = {
        'recent_trips': recent_trips,
        'favorite_itineraries': favorite_itineraries,
        'stats': {
            'total_trips': total_trips,
            'completed_trips': completed_trips,
            'processing_trips': processing_trips,
            'failed_trips': failed_trips,
            'recent_activity': recent_activity,
            'total_budget': total_budget,
        },
        'top_destinations': top_destinations,
        'travel_styles': travel_styles,
    }
    
    return render(request, 'users/dashboard.html', context)


def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')