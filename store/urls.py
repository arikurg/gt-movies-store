from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    
    path('review/<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review_edit'),
    path('review/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),

    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:movie_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
]