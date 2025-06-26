import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth import logout
from .models import User
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    UserProfileSerializer, UserListSerializer
)
from .permissions import IsAdminLawyer

# Initialize loggers
auth_logger = logging.getLogger('legal_backend.auth')
audit_logger = logging.getLogger('legal_backend.audit')


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that returns user info along with tokens
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', 'unknown')
        client_ip = self.get_client_ip(request)
        
        try:
            serializer = UserLoginSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            # Log successful login
            auth_logger.info(
                f"LOGIN_SUCCESS | User: {user.email} | "
                f"Role: {user.role} | "
                f"IP: {client_ip} | "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
            )
            
            # Audit log
            audit_logger.info(
                f"AUDIT | Action: LOGIN | "
                f"User: {user.email} | "
                f"Role: {user.role} | "
                f"IP: {client_ip} | "
                f"Status: SUCCESS"
            )
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'lawyer_profile_id': user.lawyer_profile.id if user.lawyer_profile else None,
                }
            })
            
        except Exception as e:
            # Log failed login attempt
            auth_logger.warning(
                f"LOGIN_FAILED | Email: {email} | "
                f"IP: {client_ip} | "
                f"Error: {str(e)} | "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
            )
            
            # Audit log for failed attempt
            audit_logger.warning(
                f"AUDIT | Action: LOGIN_FAILED | "
                f"Email: {email} | "
                f"IP: {client_ip} | "
                f"Error: {str(e)[:100]}"
            )
            
            raise  # Re-raise the exception to maintain normal error handling

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegistrationView(generics.CreateAPIView):
    """
    Register a new user account.
    Only admin lawyers can create new accounts.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAdminLawyer]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log user creation
        auth_logger.info(
            f"USER_CREATED | New User: {user.email} | "
            f"Role: {user.role} | "
            f"Created By: {request.user.email} | "
            f"IP: {self.get_client_ip(request)}"
        )
        
        # Audit log
        audit_logger.info(
            f"AUDIT | Action: CREATE_USER | "
            f"New User: {user.email} | "
            f"Role: {user.role} | "
            f"Created By: {request.user.email} | "
            f"IP: {self.get_client_ip(request)}"
        )
        
        return Response({
            'message': 'User created successfully',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View and update user profile.
    Users can only access their own profile unless they're admin.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Allow admins to view any user profile via query param
        user_id = self.request.query_params.get('user_id')
        if user_id and self.request.user.is_admin_lawyer:
            return generics.get_object_or_404(User, id=user_id)
        return self.request.user


class UserListView(generics.ListAPIView):
    """
    List all users. Only accessible by admin lawyers.
    """
    queryset = User.objects.all().select_related('lawyer_profile')
    serializer_class = UserListSerializer
    permission_classes = [IsAdminLawyer]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by role if specified
        role = self.request.query_params.get('role')
        if role in ['admin', 'lawyer']:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('last_name', 'first_name')


class LinkLawyerProfileView(APIView):
    """
    Link a user account to a lawyer profile.
    Only admin lawyers can perform this action.
    """
    permission_classes = [IsAdminLawyer]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        lawyer_id = request.data.get('lawyer_id')
        
        if not user_id or not lawyer_id:
            return Response(
                {'error': 'Both user_id and lawyer_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            
            # Import here to avoid circular imports
            from core.models import Lawyer
            lawyer = Lawyer.objects.get(id=lawyer_id)
            
            # Check if lawyer is already linked to another user
            if hasattr(lawyer, 'user_account') and lawyer.user_account != user:
                return Response(
                    {'error': 'This lawyer is already linked to another user account'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.lawyer_profile = lawyer
            user.save()
            
            return Response({
                'message': f'Successfully linked {user.get_full_name()} to {lawyer.name}',
                'user': UserProfileSerializer(user).data
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Lawyer not found: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout the current user and blacklist their refresh token
    """
    user_email = request.user.email if request.user else 'unknown'
    client_ip = get_client_ip(request)
    
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                # Create RefreshToken object and blacklist it
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as token_error:
                # If blacklist fails, try alternative approach
                auth_logger.warning(
                    f"TOKEN_BLACKLIST_FAILED | User: {user_email} | "
                    f"IP: {client_ip} | "
                    f"Error: {str(token_error)}"
                )
                # Continue with logout anyway - token will expire naturally
        
        # Log successful logout
        auth_logger.info(
            f"LOGOUT_SUCCESS | User: {user_email} | "
            f"IP: {client_ip}"
        )
        
        # Audit log
        audit_logger.info(
            f"AUDIT | Action: LOGOUT | "
            f"User: {user_email} | "
            f"IP: {client_ip} | "
            f"Status: SUCCESS"
        )
        
        logout(request)
        return Response({'message': 'Successfully logged out'})
    except Exception as e:
        # Log failed logout
        auth_logger.warning(
            f"LOGOUT_FAILED | User: {user_email} | "
            f"IP: {client_ip} | "
            f"Error: {str(e)}"
        )
        
        # Return success anyway - better user experience
        # Token will expire naturally if blacklist fails
        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )


def get_client_ip(request):
    """Get the client's IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    """
    Get current authenticated user info
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)