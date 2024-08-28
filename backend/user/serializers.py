from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from .models import CustomUser

from django.utils import timezone

from .models import OTP, CustomUser

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    '''Serializer to get and update a user's details.'''

    class Meta:
        model = CustomUser
        fields = '__all__'


class CreateAccountSerializer(serializers.ModelSerializer):
    ''' Serializer to create new user '''

    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'first_name', 'last_name', 'phone_number']
        read_only_fields = ['id']        
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        '''Account creation validation function'''

        # validate password
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'error': 'Your passwords do not match'}, code=status.HTTP_400_BAD_REQUEST)
        
        # check if email exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'error': 'Email already exists'}, code=status.HTTP_400_BAD_REQUEST)
        
        # check if email exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({'error': 'Username already exists'}, code=status.HTTP_400_BAD_REQUEST)
        
        # validate password
        validate_password(data['password'])
        
        return data
    
    def create(self, validated_data):
        '''Account creation function'''
        
        password = validated_data.get('password')
        # Remove data that is not useful
        validated_data.pop('password2')

        account = User.objects.create(**validated_data)
        account.set_password(raw_password=password)
        account.save()
        
        # Create token for user although not necessary
        Token.objects.create(user=account)
        
        # TODO: Create wallet for user

        return account
    

class SendOTPSerializer(serializers.Serializer):
    '''Serializer to resend OTP verifiaction'''
    
    email = serializers.EmailField(required=True)
        
    def validate(self, data):
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'error': 'This user does not exist'}, code=status.HTTP_404_NOT_FOUND)
        
        return data
    

class VerifyAccountSerializer(serializers.Serializer):
    '''Serializer for a user to veirfy their account'''
    
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)
    
    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'User not found. Unknown email entered'}, code=status.HTTP_404_NOT_FOUND)

        all_otps = OTP.objects.filter(email=data['email'], otp=data['otp'], otp_type='signup')
        
        # Check if there is an instance of the OTP available
        if not all_otps.exists():
            raise serializers.ValidationError({'error': 'Invalid OTP entered'}, code=status.HTTP_400_BAD_REQUEST)
        
        # Loop through all OTP instances and break when a valid OTP is found 
        valid_otp = None
        for otp in all_otps:
            if not otp.is_expired():
                valid_otp = otp
                break
        
        if valid_otp is None:
            raise serializers.ValidationError({'error': 'OTP is expired'}, code=status.HTTP_400_BAD_REQUEST)
        
        return data


class LoginSerializer(serializers.Serializer):
    '''Serializer to log in a user.'''

    email_or_username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    
    def validate(self, data):
        '''Authentication validation function'''
        email_or_username = data.get('email_or_username')
        password = data.get('password')

        User = get_user_model()

        # Find the user by email
        user = User.objects.filter(email=email_or_username).first()
        if not user:
            # If not found by email, try by username
            user = User.objects.filter(username=email_or_username).first()

        if user and user.check_password(password):
            if not user.is_verified:
                raise serializers.ValidationError({'error': 'Email is not verified'}, code=status.HTTP_400_BAD_REQUEST)
            elif not user.is_active:
                raise serializers.ValidationError({'error': 'This user is not active'}, code=status.HTTP_400_BAD_REQUEST)
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Response data
            return {
                'message': f'Welcome {user.email}',
                'token': token.key,
            }
        else:
            raise serializers.ValidationError({'error': 'Invalid credentials'}, code=status.HTTP_400_BAD_REQUEST)


class UserDetailsSerializer(serializers.ModelSerializer):
    '''Serializer to get and update a user's details.'''

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'reading_stage',  'reading_star', 'is_verified', 'is_staff']        
    
    def update(self, instance, validated_data):
        '''Update details function'''

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    '''Serializer to change user password.'''

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def update(self, instance, validated_data):
        email = validated_data.get('email')
        old_password = validated_data.get('password')
        new_password = validated_data.get('new_password')
        confirm_password = validated_data.get('confirm_password')

        user = authenticate(email=email, password=old_password)
        current_user = self.context['request'].user

        if user is None:
            raise serializers.ValidationError({'error': 'User credentials incorrect. Check your email and password and try again.'}, code=status.HTTP_400_BAD_REQUEST)
        if user.email != current_user.email:
            raise serializers.ValidationError({'error': 'User credentials incorrect. Check your email and password and try again.'}, code=status.HTTP_400_BAD_REQUEST)
        elif old_password == new_password:
            raise serializers.ValidationError({'error': 'New password cannot be the same as old password.'}, code=status.HTTP_400_BAD_REQUEST)
        elif new_password != confirm_password:
            raise serializers.ValidationError({'error': 'New password and confirm password field has to be the same.'}, code=status.HTTP_400_BAD_REQUEST)
        
        validate_password(new_password)
        instance.set_password(new_password)

        instance.save()

        return instance
    

class RequestPasswordResetSerializer(serializers.Serializer):
    '''Serializer to reset user password'''
    
    email = serializers.EmailField(required=True)
    
    def validate(self, data):
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'error': 'This email does not exist'}, code=status.HTTP_404_NOT_FOUND)
        
        return data
    

class VerifyOTPForPasswordResetSerializer(serializers.Serializer):
    '''Serializer for a user to veirfy their account'''
    
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)
    
    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'User not found. Unknown email entered'}, code=status.HTTP_404_NOT_FOUND)

        all_otps = OTP.objects.filter(email=data['email'], otp=data['otp'], otp_type='passwordreset')
        
        # Check if there is an instance of the OTP available
        if not all_otps.exists():
            raise serializers.ValidationError({'error': 'Invalid OTP entered'}, code=status.HTTP_400_BAD_REQUEST)
        
        # Loop through all OTP instances and break when a valid unexpired OTP is found 
        valid_otp = None
        for otp in all_otps:
            if not otp.is_expired():
                valid_otp = otp
                break
        
        if valid_otp is None:
            raise serializers.ValidationError({'error': 'OTP is expired'}, code=status.HTTP_400_BAD_REQUEST)
        
        return data
    

class PasswordResetSerializer(serializers.Serializer):
    '''Serializer to reset password'''
    
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def update(self, instance, validated_data):
        if validated_data['new_password'] != validated_data['confirm_password']:
            raise serializers.ValidationError({'error': 'New password and confirm password field has to be the same.'}, code=status.HTTP_400_BAD_REQUEST)
        
        validate_password(validated_data['new_password'])
        instance.set_password(validated_data['new_password'])

        instance.save()

        return instance

    
class ChangeEmailSerializer(serializers.Serializer):
    '''Serializer to change user email'''
    
    email = serializers.EmailField(required=True)
    
    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'error': 'This email already exists'}, code=status.HTTP_400_BAD_REQUEST)
        
        return data
    
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
            
        instance.save()
        return instance
