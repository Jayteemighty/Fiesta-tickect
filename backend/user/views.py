import os, random
from dotenv import load_dotenv
from pathlib import Path

from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.views import View

import requests
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.response import Response
from .models import CustomUser
from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from .serializers import UserSerializer

from . import serializers
from .models import OTP, CustomUser
from .util import Util
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import status
from django.contrib.auth.models import User

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

User = get_user_model()


def send_verification_email(email):
    '''Function to send verification email'''
    
    user = User.objects.get(email=email)
    
    otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    OTP.objects.create(email=user.email, otp=otp, otp_type='signup')
    
    subject = 'Welcome! Verify your email address'
    body = f'Hi, {user.first_name}.\n\nThanks for signing up on LaFiesta Tickets.\nThis is your OTP to verify your account:\n{otp}.\n\nThe OTP expires after 10 minutes.\n\nIf you did not request for this OTP, kindly ignore.\nThank you.'
    
    Util.send_email(user.email, subject, body)
    

def send_password_reset_email(email):
    '''Function to send password reset email'''
    
    user = User.objects.get(email=email)
    
    otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    OTP.objects.create(email=user.email, otp=otp, otp_type='passwordreset')
    
    subject = 'Password reset'
    body = f'Hi, {user.first_name}.\n\nThanks for choosing LaFiesta Tickets.\nThis is your OTP to reset your password:\n{otp}\n\nThe OTP expires after 10 minutes..\n\nIf you did not request for this OTP, kindly ignore.\nThank you.'
    
    Util.send_email(user.email, subject, body)


# Google auth views
class GoogleAuthRedirect(APIView):
    '''View for a user to sign up on google'''
    
    permission_classes = []
    
    def get(self, request):
        redirect_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}&response_type=code&scope=https://www.googleapis.com/auth/userinfo.profile%20https://www.googleapis.com/auth/userinfo.email&access_type=offline&redirect_uri={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}"
        
        return redirect(redirect_url)
    

class GoogleRedirectURIView(APIView):
    '''View to handle google user creation'''
    
    permission_classes = []
    
    def get(self, request):
        # Extract the authorization code from the request URL
        code = request.GET.get('code')
        
        if code:
            # Prepare the request parameters to exchange the authorization code for an access token
            token_endpoint = 'https://oauth2.googleapis.com/token'
            token_params = {
                'code': code,
                'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'redirect_uri': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI,  # Must match the callback URL configured in your Google API credentials
                'grant_type': 'authorization_code',
            }
            
            # Make a POST request to exchange the authorization code for an access token
            response = requests.post(token_endpoint, data=token_params)
            
            if response.status_code == 200:
                access_token = response.json().get('access_token')
                
                if access_token:
                    # Make a request to fetch the user's profile information
                    profile_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'
                    headers = {'Authorization': f'Bearer {access_token}'}
                    profile_response = requests.get(profile_endpoint, headers=headers)
                    
                    if profile_response.status_code == 200:
                        data = {}
                        profile_data = profile_response.json()
                        print(profile_data)
                        
                        user = User.objects.filter(email=profile_data['email']).first()
                        
                        # Check if user exists already so they can just login
                        if user:
                            # Check if user is verified to login
                            if not user.is_verified:
                                return Response({'error': 'Verify your account to continue'}, status=status.HTTP_403_FORBIDDEN)
                            
                            token, created = Token.objects.get_or_create(user=user)
                            data['token'] = str(token.key) 
                            return Response(data, status.HTTP_200_OK) 
                        
                        # Proceed with user creation or login
                        new_user = User.objects.create(
                            first_name=profile_data["given_name"],
                            email=profile_data["email"],
                            password=None,
                            is_verified=profile_data['verified_email'],
                            sign_up_mode='google'
                        )
                        new_user.set_password(None)
                        
                        if "family_name" in profile_data:
                            new_user.last_name = profile_data["family_name"]
                            new_user.save()
                            
                        token, created = Token.objects.get_or_create(user=new_user)
                        
                        data['user'] = {
                            'first_name': new_user.first_name,
                            'last_name': new_user.last_name,
                            'email': new_user.email,
                        }
                        data['token'] = str(token.key)
                        return Response(data, status.HTTP_201_CREATED)
        
        return Response({}, status.HTTP_400_BAD_REQUEST)

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
    
class RegisterView(generics.GenericAPIView):
    '''View to register users'''

    serializer_class = serializers.CreateAccountSerializer
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        try:
            send_verification_email(email=serializer.data['email'])
            
        except Exception as e:
            return Response({
                'exception': f'{e}',
                'error': 'could not send emailAn error occured. Try again later',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
 

class VerifyAccountView(generics.GenericAPIView):
    '''View to verify account'''
    
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers.VerifyAccountSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = User.objects.get(email=serializer.data['email'])
        
        user.is_verified = True
        user.save()
        
        return Response({'message': 'Account verified successfully'}, status=status.HTTP_200_OK)
            

class ResendVerificationEmailView(generics.GenericAPIView):
    '''View to resend verification email'''
    
    serializer_class = serializers.SendOTPSerializer
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = User.objects.get(email=serializer.data['email'])
            if user.is_verified:
                return Response({'error': 'You have been verified already'}, status=status.HTTP_400_BAD_REQUEST)
            
            send_verification_email(email=serializer.data['email'])
            
        except Exception as e:
            return Response({
                'exception': f'{e}',
                'error': 'An error occured. Try again later',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': f"Verification email sent successfully. Check {serializer.data['email']} for an OTP"},
            status=status.HTTP_201_CREATED
        )

class LoginView(generics.GenericAPIView):
    '''View to login users'''
    
    serializer_class = serializers.LoginSerializer
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

        

class UserDetailsView(generics.RetrieveUpdateAPIView):
    '''View to get, and update user account'''
    
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserDetailsSerializer
    
    def get_object(self):
        return self.request.user
    

class ChangeEmailView(generics.UpdateAPIView):
    ''' View to change user email address'''
    
    serializer_class = serializers.ChangeEmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            super().update(request, *args, **kwargs)
            # send email verification to new email
            send_verification_email(email=serializer.data['email'])
            
            # Get user details
            user = User.objects.get(id=self.request.user.id)
                        
            # Make user unverifed because of change in email
            user.is_verified = False
            user.save()            
            
        except Exception as e:
            return Response({
                'exception': f'{e}',
                'error': 'An error occured. Try again later',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': f"Email changed successfully. Check {serializer.data['email']} for a new email verification link"},
            status=status.HTTP_201_CREATED
        )


class ChangePasswordView(generics.UpdateAPIView):
    '''View to change user password'''

    serializer_class = serializers.ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    

class RequestPasswordResetView(generics.GenericAPIView):
    '''View for a user to request for a password reset'''
    
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.SendOTPSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Send password reset email that should send an OTP to allow resetting the password
        send_password_reset_email(serializer.data['email'])
        
        return Response({'message': f"Check {serializer.data['email']} for a password reset link"}, status=status.HTTP_200_OK)


class VerifyPasswordResetView(generics.GenericAPIView):
    '''View for a user to verify password reset OTP'''
    
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.VerifyOTPForPasswordResetSerializer   
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({'message': 'Proceed to change your password'}, status=status.HTTP_200_OK)
     
     
class PasswordResetView(generics.UpdateAPIView):
    '''View for a user to request a password reset'''

    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.PasswordResetSerializer

    def get_object(self):
        email = self.request.data.get('email')
        if not email:
            raise ValidationError({'error': 'Email field is required.'}, code=status.HTTP_400_BAD_REQUEST)
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({'error': 'User with this email does not exist.'}, code=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    ''' View to logout users'''
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # get current user
        current_user = request.user

        # get token based on current user
        current_user_token = Token.objects.get(user=current_user)
        # delete token
        current_user_token.delete()
        
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    

class DeleteAccountView(APIView):
    '''View to delete a user's account. This will just make the user's account inactive.'''
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        user.is_active = False
        
        user.save()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)



class UserListView(generics.ListAPIView):
    """ Endpoint to get all user details. """
    
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.all()

    
    
class UpdateDetailsView(APIView):
    """ Endpoint to update user reading level and star on book completion. """
    
    permission_classes = [IsAuthenticated]
    def put(self, request):
        user = request.user
        user.update_levels()
        
        return Response({
            "message" : "Update successful!",
            "Reading Stage" : user.reading_stage,
            "Reading Star" : user.reading_star
            }, status=status.HTTP_202_ACCEPTED)
