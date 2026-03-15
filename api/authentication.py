from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


class TokenQueryParamAuthentication(TokenAuthentication):
    """
    Extends TokenAuthentication to also accept token via query parameter.
    This is needed for <img src> tags that cannot send Authorization headers.
    Usage: /api/secure-profile/2/?token=abc123
    """

    def authenticate(self, request):
        # First try standard header-based auth
        result = super().authenticate(request)
        if result is not None:
            return result

        # Fallback: check query parameter
        token_key = request.query_params.get('token')
        if not token_key:
            return None

        try:
            token = Token.objects.get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')

        return (token.user, token)
