from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login con username e password, restituisce token JWT e profilo utente."""
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username e password sono obbligatori.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Credenziali non valide.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Account disattivato.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Genera token JWT
    refresh = RefreshToken.for_user(user)
    serializer = UserSerializer(user)

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Restituisce il profilo dell'utente autenticato con permessi."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Blacklist del refresh token per logout."""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'message': 'Logout effettuato.'})
