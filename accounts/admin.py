from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Product, CartItem, Order, OrderItem


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Қосымша', {'fields': ('phone_number', 'bio', 'profile_photo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Қосымша', {'fields': ('email', 'phone_number', 'bio', 'profile_photo')}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'price', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('id',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'cart_total_price', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)

    def cart_total_price(self, obj):
        return obj.total_price
    cart_total_price.short_description = 'Жалпы сумма'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'product_name', 'price', 'quantity', 'total_price_display')
    readonly_fields = ('total_price_display',)

    def total_price_display(self, obj):
        if not obj or obj.pk is None:
            return '-'
        return obj.total_price
    total_price_display.short_description = 'Жалпы сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    inlines = [OrderItemInline]


admin.site.register(CustomUser, CustomUserAdmin)