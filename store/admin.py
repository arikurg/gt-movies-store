from django.contrib import admin
from .models import Movie, Review, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['movie']


@admin.action(description='Un-report selected reviews')
def unreport_reviews(modeladmin, request, queryset):
    queryset.update(is_reported=False)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('movie', 'user', 'created_at', 'is_reported')
    list_filter = ('is_reported', 'created_at')
    actions = [unreport_reviews]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'created_at']
    list_filter = ['created_at', 'user']
    inlines = [OrderItemInline]

admin.site.register(Movie)
admin.site.register(Review, ReviewAdmin)




# super user login info
# username: movieStoreAdmin
# email: ariel.khurgin@gmail.com
# password: adminpassword