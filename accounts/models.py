from django.db import models
from django.contrib.auth.models import AbstractUser


def user_avatar_path(instance, filename):
    return f'profile_photos/user_{instance.id}/{filename}'


def product_image_path(instance, filename):
    return f'products/{instance.slug}/{filename}'


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(upload_to=user_avatar_path, blank=True, null=True)

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        if self.profile_photo:
            return self.profile_photo.url
        return '/media/default/default-avatar.png'


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('study', 'Оқу'),
        ('gaming', 'Ойын'),
        ('work', 'Жұмыс'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    price = models.PositiveIntegerField()
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='study')

    processor = models.CharField(max_length=255)
    ram = models.CharField(max_length=100)
    storage = models.CharField(max_length=100)
    screen = models.CharField(max_length=100)
    gpu = models.CharField(max_length=255, blank=True, null=True)

    image_main = models.ImageField(upload_to=product_image_path)
    image_2 = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    image_3 = models.ImageField(upload_to=product_image_path, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.quantity})'

    @property
    def total_price(self):
        return (self.product.price or 0) * (self.quantity or 0)


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Жаңа'),
        ('processing', 'Өңделуде'),
        ('paid', 'Төленді'),
        ('completed', 'Аяқталды'),
        ('cancelled', 'Бас тартылды'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.id} - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.product_name} ({self.quantity})'

    @property
    def total_price(self):
        price = self.price or 0
        quantity = self.quantity or 0
        return price * quantity