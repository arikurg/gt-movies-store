from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Movie, Review, Order, OrderItem, Rating, Profile, RATING_ORDER
from .forms import CustomUserCreationForm, ReviewForm, ProfileUpdateForm
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.contrib import messages  # <--- IMPORTED MESSAGES FRAMEWORK

# General Views
def home(request):
    return render(request, 'home.html') # US 1

def movie_list(request):
    query = request.GET.get('q')

    # 1. Get all movies based on search query
    if query:
        movies = Movie.objects.filter(title__icontains=query)
    else:
        movies = Movie.objects.all()

    # 2. Get the user's maximum allowed rating setting
    max_allowed_rating_value = 100 # Default to high number (unrestricted) if not logged in

    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            # Get the string rating (e.g., 'PG-13')
            max_rating_str = profile.max_content_rating
            # Convert the user's max setting to its numeric index
            max_allowed_rating_value = RATING_ORDER.index(max_rating_str)
        except Profile.DoesNotExist:
            pass

    context = {
        'movies': movies,
        'max_allowed_rating_value': max_allowed_rating_value,
        'rating_order': RATING_ORDER,
    }
    return render(request, 'store/movie_list.html', context)

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)

    # --- START: SECURITY CHECK FOR CONTENT RATING ---
    # Even if the link is disabled in the frontend, we must block direct access here.
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            max_rating_str = profile.max_content_rating
            max_allowed_rating_value = RATING_ORDER.index(max_rating_str)
            
            # Calculate this movie's rating value
            movie_rating_value = movie.get_rating_value()
            
            if movie_rating_value > max_allowed_rating_value:
                # Content is restricted for this user
                messages.error(request, f"Access Denied: The content rating of '{movie.content_rating}' exceeds your maximum allowed setting.")
                return redirect('movie_list')
                
        except Profile.DoesNotExist:
            pass
    # --- END: SECURITY CHECK ---

    reviews = movie.reviews.filter(is_reported=False)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.save() # US 8
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = ReviewForm()
        
    return render(request, 'store/movie_detail.html', {'movie': movie, 'reviews': reviews, 'form': form}) # US 13

@login_required
@require_POST
def report_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_reported = True
    review.save()
    return redirect('movie_detail', pk=review.movie.pk)

# User Authentication
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html' # US 2

# Review CRUD
class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Review
    fields = ['comment']
    template_name = 'store/review_edit.html'
    
    def get_success_url(self):
        review = self.get_object()
        return reverse_lazy('movie_detail', kwargs={'pk': review.movie.pk})

    def test_func(self): # US 10
        review = self.get_object()
        return self.request.user == review.user

class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'store/review_confirm_delete.html'
    
    def get_success_url(self):
        review = self.get_object()
        return reverse_lazy('movie_detail', kwargs={'pk': review.movie.pk})

    def test_func(self): # US 11
        review = self.get_object()
        return self.request.user == review.user

# Shopping Cart
@login_required
def add_to_cart(request, movie_id): # US 7
    movie = get_object_or_404(Movie, id=movie_id)
    cart = request.session.get('cart', {})
    
    cart[str(movie_id)] = cart.get(str(movie_id), 0) + 1
    request.session['cart'] = cart
    return redirect('view_cart')

@login_required
def view_cart(request): # US 6
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    for movie_id, quantity in cart.items():
        movie = get_object_or_404(Movie, id=movie_id)
        item_total = movie.price * quantity
        cart_items.append({'movie': movie, 'quantity': quantity, 'total': item_total})
        total_price += item_total
    
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def clear_cart(request): # US 9
    request.session['cart'] = {}
    return redirect('view_cart')

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('movie_list')

    total_price = 0
    for movie_id, quantity in cart.items():
        movie = get_object_or_404(Movie, id=movie_id)
        total_price += movie.price * quantity
    
    order = Order.objects.create(user=request.user, total_price=total_price)
    
    for movie_id, quantity in cart.items():
        movie = get_object_or_404(Movie, id=movie_id)
        OrderItem.objects.create(order=order, movie=movie, quantity=quantity, price=movie.price)
    
    request.session['cart'] = {}
    return redirect('order_history')

@login_required
def order_history(request): # US 14
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
@require_POST
def rate_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    rating_value = request.POST.get('rating')

    if rating_value:
        Rating.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'value': int(rating_value)}
        )

    return redirect('movie_detail', pk=pk)

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if p_form.is_valid():
            p_form.save()
            return redirect('profile') 
    else:
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'p_form': p_form,
        'profile': profile
    }
    return render(request, 'store/profile.html', context)