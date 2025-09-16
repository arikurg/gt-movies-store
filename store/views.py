from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Movie, Review, Order, OrderItem
from .forms import CustomUserCreationForm, ReviewForm
from django.views.decorators.http import require_POST

# General Views
def home(request):
    return render(request, 'home.html') # US 1

def movie_list(request):
    query = request.GET.get('q')
    if query:
        movies = Movie.objects.filter(title__icontains=query) # US 5
    else:
        movies = Movie.objects.all()
    return render(request, 'store/movie_list.html', {'movies': movies}) # US 4

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
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
@require_POST # This ensures only POST requests can access this view
def report_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_reported = True
    review.save()
    # Redirect back to the movie detail page. The review will now be hidden.
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
    
    request.session['cart'] = {} # Clear cart after checkout
    return redirect('order_history')

@login_required
def order_history(request): # US 14
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})
# Create your views here.
