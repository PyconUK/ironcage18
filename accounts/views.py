import random

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegisterForm


def assign_a_snake(user):
    STANDARD_SNAKES = [
        ('blue', 'deerstalker'),
        ('purple', 'bowie'),
        ('red', 'glasses'),
        ('green', 'dragon'),
        ('yellow', 'mortar'),
        ('orange', 'astronaut'),
    ]

    colour, extra = random.choice(STANDARD_SNAKES)

    user.badge_snake_colour = colour
    user.badge_snake_extras = extra

    user_ticket = user.get_ticket()
    if user_ticket and user_ticket.rate == "corporate":
        user.badge_company = user_ticket.order_company_name()

    user.save()


@login_required
def profile(request):
    user = request.user

    if user.badge_snake_colour in [None, ''] or user.badge_snake_extras in [None, '']:
        assign_a_snake(user)

    context = {
        'is_organiser': request.user.is_organiser,
        'is_contributor': request.user.is_contributor,
        'name': user.name,
        'js_paths': ['accounts/badges.js'],
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    user_ticket = request.user.get_ticket()

    if request.user.badge_snake_colour in [None, ''] or request.user.badge_snake_extras in [None, '']:
        assign_a_snake(request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    context = {
        'is_organiser': request.user.is_organiser,
        'is_contributor': request.user.is_contributor,
        'ticket_rate': user_ticket.rate if user_ticket else '',
        'form': form,
        'js_paths': ['accounts/profile_form.js', 'accounts/badges.js'],
    }

    return render(request, 'accounts/edit_profile.html', context)


def register(request):
    if request.user.is_authenticated:
        messages.error(request, 'You are already signed in!')
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                username=user.email_addr,
                password=form.cleaned_data['password1']
            )
            login(request, user)

            return redirect(request.POST.get('next', 'index'))

    else:
        form = RegisterForm()

    context = {
        'form': form,
        'next': request.GET.get('next', 'index'),
    }

    return render(request, 'registration/register.html', context)


def legal(request):
    return render(request, 'registration/legal.html')
