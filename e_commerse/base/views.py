
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from orders.models import Order, OrderItems
from seller.models import Seller
from django.contrib import messages
from django.utils.timezone import now
from .models import OTP
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from .forms import UserProfileForm
from orders.forms import ProductReviewForm
from .utils import validate_phone_number, generate_otp  # Assuming you have these utility functions
from .models import Userprofile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render
from store.models import Product

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request, exception):
    return render(request, '500.html', status=500)


def login_or_signup_with_otp(request):
    context = {}
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        otp = request.POST.get('otp')
        action = request.POST.get('action')  # Distinguish between 'send' and 'resend'

        # Validate phone number
        phone_number = validate_phone_number(phone_number)
        if not phone_number:
            messages.error(request, "Invalid phone number.")
            return render(request, 'register/login_or_signup.html', context)

        # OTP submission
        if otp:
            try:
                otp_record = OTP.objects.get(phone_number=phone_number)
                if otp_record.otp == otp and otp_record.is_valid():
                    # OTP is valid
                    user, created = User.objects.get_or_create(username=phone_number)
                    if created:
                        random_password = get_random_string(length=8)  # You can adjust the length as needed
                        user.set_password(random_password)
                        user.save()
                        messages.success(request, "Account created and logged in successfully.")
                    else:
                        messages.success(request, "Logged in successfully.")

                    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['not_admin'] = True
                    otp_record.delete()  # Clear OTP after use
                    return redirect('home')
                else:
                    messages.error(request, "Invalid or expired OTP.")
            except OTP.DoesNotExist:
                messages.error(request, "OTP not found. Please request a new one.")

        # Request OTP or Resend OTP
        elif action in ['send', 'resend']:
            otp_record, created = OTP.objects.get_or_create(phone_number=phone_number)

            if action == 'resend' and not otp_record.can_resend():
                if otp_record.resend_count >= 3:
                    messages.error(request, "Maximum OTP resend attempts reached for today.")
                else:
                    messages.error(request, "You can resend OTP only after 1 minute.")
                return render(request, 'register/login_or_signup.html', context)

            # Generate and send OTP
            otp = generate_otp()
            otp_record.otp = otp
            otp_record.created_at = now()
            if action == 'resend':
                otp_record.resend_count += 1
                otp_record.last_resend_at = now()
            otp_record.save()

            # Simulate sending OTP (replace with SMS API in production)
            # print(f"""-----------------------------
            #       Sending OTP {otp} to {phone_number}
            #       -----------------------------""")
            messages.info(request, "OTP sent to your phone number.otp is {}".format(otp))

            context['otp'] = otp
            context['otp_sent'] = True
            context['phone_number'] = phone_number
            

    return render(request, 'register/login_or_signup.html', context)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Userprofile.objects.create(user=instance, phone_number=instance.username)


@login_required
def update_profile(request):
    try:
        profile = request.user.userprofile
    except Userprofile.DoesNotExist:
        profile = Userprofile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_account')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'useraccount/update_profile.html', {'form': form})

@login_required
def account_page(request):
    user = request.user
    userprofile = user.userprofile
    orders = Order.objects.filter(buyer=user)
    purchased_products = orders.filter(status="Delivered")

    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        product_id = request.POST.get('product_id')
        print("""Product ID: """,product_id)
        if not product_id:
            # Handle missing product ID
            # return render(request, 'error.html', {'message': 'Product ID is missing.'})
            return redirect('user_account')
        
        product = get_object_or_404(Product, id=product_id)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('user_account')
    else:
        form = ProductReviewForm()
    return render(request, 'useraccount/user_account.html', {
        'user': user,
        'userprofile': userprofile,
        'orders': orders,
        'purchased_products': purchased_products,
        'form': form
    })

@login_required
def become_seller(request):
    if hasattr(request.user, 'seller_profile'):
        messages.info(request, "You are already registered as a seller.")
        return redirect('home')  # Redirect to a dashboard or relevant page

    if request.method == 'POST':
        owner_name = request.POST.get('owner_name')
        shop_name = request.POST.get('shop_name')
        shop_address = request.POST.get('shop_address')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        if owner_name and shop_name and shop_address and email and phone:
            seller = Seller.objects.create(
                user=request.user,
                owner_name=owner_name,
                shop_name=shop_name,
                shop_address=shop_address,
                email=email,
                phone=phone
            )
            messages.success(request, "You are now a seller!")
            return redirect('home')  # Redirect to a dashboard or relevant page
        else:
            messages.error(request, "All fields are required.")

    return render(request, 'register/become_seller.html')