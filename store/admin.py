from django.contrib import admin
from .models import Movie, Review, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['movie']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'created_at']
    list_filter = ['created_at', 'user']
    inlines = [OrderItemInline]

admin.site.register(Movie)
admin.site.register(Review)


# super user login info
# username: movieStoreAdmin
# email: ariel.khurgin@gmail.com
# password: adminpassword