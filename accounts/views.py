import json
import os

import google.generativeai as genai

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .forms import RegisterForm, ProfileUpdateForm, CustomPasswordChangeForm
from .models import Product, CartItem, Order, OrderItem


# API key
genai.configure(api_key=settings.GEMINI_API_KEY)


def get_working_gemini_model():
    """
    Қол жетімді generateContent модельдерінің ішінен біреуін автоматты таңдайды.
    404 model not found проблемасын азайту үшін.
    """
    preferred = [
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-pro",
    ]

    try:
        available = []
        for m in genai.list_models():
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods:
                available.append(m.name)

        for model_name in preferred:
            if model_name in available:
                return genai.GenerativeModel(model_name=model_name)

        if available:
            return genai.GenerativeModel(model_name=available[0])

    except Exception:
        pass

    # Соңғы fallback
    return genai.GenerativeModel(model_name="models/gemini-1.5-flash")


def home(request):
    products = Product.objects.filter(is_active=True).order_by("id")
    return render(request, "accounts/home.html", {"products": products})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    error = ""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("profile")
        else:
            error = "Қате логин немесе пароль"

    return render(request, "accounts/login.html", {"error": error})


@login_required
def profile_view(request):
    profile_message = ""
    password_message = ""

    if request.method == "POST":
        if "save_profile" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)

            if profile_form.is_valid():
                profile_form.save()
                profile_message = "Профиль сақталды."

        elif "change_password" in request.POST:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                password_message = "Пароль өзгертілді."
        else:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)
    else:
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "profile_message": profile_message,
            "password_message": password_message,
        },
    )


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def add_to_cart_view(request, slug):
    if request.method != "POST":
        return redirect("home")

    product = get_object_or_404(Product, slug=slug, is_active=True)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"quantity": 1},
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart")


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related("product")
    total_price = sum(item.total_price for item in cart_items)

    return render(
        request,
        "accounts/cart.html",
        {
            "items": cart_items,
            "total_price": total_price,
        },
    )


@login_required
def remove_from_cart_view(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        item.delete()
    return redirect("cart")


@login_required
def clear_cart_view(request):
    if request.method == "POST":
        CartItem.objects.filter(user=request.user).delete()
    return redirect("cart")


@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related("product")
    total_price = sum(item.total_price for item in cart_items)

    if request.method == "POST":
        if cart_items.exists():
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                status="new",
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity,
                )

            cart_items.delete()
            return redirect("my_orders")

    return render(
        request,
        "accounts/checkout.html",
        {
            "items": cart_items,
            "total_price": total_price,
        },
    )


@login_required
def my_orders_view(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )
    return render(request, "accounts/my_orders.html", {"orders": orders})


def assistant_view(request):
    message = request.GET.get("message", "").strip()

    if not message:
        return JsonResponse(
            {
                "action": "message",
                "text": "Сұрақ бос болмауы керек.",
                "url": "",
                "slug": "",
            }
        )

    if not getattr(settings, "GEMINI_API_KEY", ""):
        return JsonResponse(
            {
                "action": "message",
                "text": "GEMINI_API_KEY табылмады.",
                "url": "",
                "slug": "",
            }
        )

    products = list(
        Product.objects.filter(is_active=True).values(
            "name",
            "slug",
            "price",
            "category",
            "processor",
            "ram",
            "storage",
            "screen",
            "gpu",
        )
    )

    if not products:
        return JsonResponse(
            {
                "action": "message",
                "text": "Қазір сайтта белсенді товарлар табылмады.",
                "url": "",
                "slug": "",
            }
        )

    product_lines = []
    for p in products:
        product_lines.append(
            f"аты: {p['name']}, "
            f"slug: {p['slug']}, "
            f"бағасы: {p['price']}, "
            f"категориясы: {p['category']}, "
            f"процессор: {p['processor']}, "
            f"ram: {p['ram']}, "
            f"жадысы: {p['storage']}, "
            f"экраны: {p['screen']}, "
            f"gpu: {p['gpu'] or 'жоқ'}"
        )

    products_text = "\n".join(product_lines)

    prompt = f"""
Сен TULGA сайт көмекшісісің.

Міндетің:
Пайдаланушының сөзін түсініп, тек жарамды JSON қайтару.

Сен тек мына форматта жауап бересің:
{{
  "action": "message немесе redirect немесе add_to_cart",
  "text": "қазақша қысқа жауап",
  "url": "redirect болса URL, әйтпесе бос жол",
  "slug": "add_to_cart болса slug, әйтпесе бос жол"
}}

Ережелер:
1. ЕШҚАНДАЙ markdown қолданба.
2. ЕШҚАНДАЙ ```json``` жазба.
3. Тек JSON қайтар.
4. Жауап қазақша болсын.
5. Егер пайдаланушы бет ашуды сұраса, action=redirect қайтар.
6. Егер пайдаланушы товарды корзинаға салуды сұраса, action=add_to_cart қайтар.
7. Егер пайдаланушы тек сұрақ қойса, action=message қайтар.
8. Егер нақты товар айтылса, тек төмендегі товарлардан тап.
9. Егер профиль ашу десе -> /profile/
10. Егер корзина ашу десе -> /cart/
11. Егер каталог ашу десе -> /#products
12. Егер техқолдау ашу десе -> /#support
13. Егер pdf ашу немесе жүктеу десе -> /#download
14. Егер тапсырыс ашу десе -> /#order
15. Егер заказдарым десе -> /my-orders/
16. Егер checkout немесе төлем десе -> /checkout/
17. Егер басты бет десе -> /
18. Егер аккаунттан шығу десе -> /logout/ үшін redirect қайтар.

Қолдануға болатын URL:
- каталог: /#products
- техқолдау: /#support
- pdf: /#download
- тапсырыс: /#order
- корзина: /cart/
- профиль: /profile/
- заказдар: /my-orders/
- checkout: /checkout/
- басты бет: /
- logout: /logout/

Сайттағы товарлар:
{products_text}

Пайдаланушы сұрағы:
{message}
"""

    try:
        gemini_model = get_working_gemini_model()
        response = gemini_model.generate_content(prompt)

        raw_text = getattr(response, "text", "").strip()
        if not raw_text:
            return JsonResponse(
                {
                    "action": "message",
                    "text": "Gemini жауап қайтармады.",
                    "url": "",
                    "slug": "",
                }
            )

        start = raw_text.find("{")
        end = raw_text.rfind("}")

        if start != -1 and end != -1:
            raw_text = raw_text[start : end + 1]

        data = json.loads(raw_text)

        action = data.get("action", "message")
        text = data.get("text", "Жауап дайын.")
        url = data.get("url", "")
        slug = data.get("slug", "")

        if action not in ["message", "redirect", "add_to_cart"]:
            action = "message"
            url = ""
            slug = ""

        if action == "message":
            url = ""
            slug = ""

        if action == "redirect":
            slug = ""

        if action == "add_to_cart" and not slug:
            action = "message"
            text = "Қай товарды корзинаға қосу керек екенін нақтылап жазыңыз."
            url = ""

        return JsonResponse(
            {
                "action": action,
                "text": text,
                "url": url,
                "slug": slug,
            }
        )

    except Exception as e:
        return JsonResponse(
            {
                "action": "message",
                "text": f"Қате шықты: {str(e)}",
                "url": "",
                "slug": "",
            }
        )