from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from users.permissions import IsCustomer
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, LoginSerializer, UserSerializer
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework import status
from .models import CustomUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.decorators import login_required
from django.urls import reverse




CustomUser = get_user_model()
def landing_page(request):
    return render(request, 'tours/index.html') 

def home_redirect(request):
    return redirect("login")

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    
def register_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']

        # Check if the email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'users/Signup.html')  # Using the correct template

        # Create new user
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=role
        )

        # Auto-login after registration
        login(request, user)
        messages.success(request, "Registration successful!")
        return redirect('dashboard')  # Redirect after successful signup

    # Consistent rendering for GET requests
    return render(request, 'users/Signup.html')



class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=400)
    
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()

        if not email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'users/login.html')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'This account is inactive. Please contact support.')
                return render(request, 'users/login.html')

            # Clear any existing session before login
            logout(request)
            login(request, user)

            # Role-Based Redirects
            if user.role == 'customer':
                return redirect('upgrade-account')  # Force upgrade for customers
            elif user.role == 'vendor':
                return redirect('vendor-dashboard')
            elif user.role == 'planner':
                return redirect('planner-dashboard')
            elif user.role == 'operator':
                return redirect('dashboard')
            elif user.role == 'admin':
                return redirect(reverse('admin:index'))  # Django admin panel

            # Fallback redirect
            return redirect('home')

        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect("login")

class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)



@api_view(['POST'])
def mobile_register_view(request):
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')

    # Validate fields
    if not all([name, email, password]):
        return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if email already exists
    if CustomUser.objects.filter(email=email).exists():
        return Response({'error': 'Email is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user as Customer by default
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        name=name,
        role='customer'  # Always 'customer' for mobile
    )

    return Response({
        'message': 'Registration successful!',
        'user_id': user.id,
        'role': user.role
    }, status=status.HTTP_201_CREATED)

class UnifiedLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
#...................................................upgrade...........................................................


@login_required
def upgrade_account(request):
    if request.method == 'POST':
        desired_role = request.POST.get('role')

        # Only allow Customers to upgrade
        if request.user.role != 'customer':
            messages.info(request, 'You already have an elevated role.')
            return redirect('home')  # Redirect to home or relevant page

        # Upgrade user role
        user = request.user
        user.role = desired_role
        user.save()

        messages.success(request, f'Your account has been upgraded to {desired_role}.')
        return redirect('home')  # Redirect to the home or dashboard after upgrade

    return render(request, 'upgrade_account.html')
