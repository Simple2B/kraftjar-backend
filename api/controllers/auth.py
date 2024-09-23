import jwt

from jwt import PyJWKClient

from app import schema as s
from config import config
from app.logger import log

CFG = config()


JWKS_CLIENT = PyJWKClient(CFG.APPLE_PUBLIC_KEY_URL)


def verify_apple_token(auth_data: s.AppleAuthTokenIn) -> s.AppleTokenVerification:
    """Verifies the Apple auth token and returns the decoded token"""
    # Fetch Apple's public keys
    signing_key = JWKS_CLIENT.get_signing_key_from_jwt(auth_data.id_token)
    apple_public_key = signing_key.key

    # Verify the signature using the fetched public key
    decoded_token_raw = jwt.decode(
        auth_data.id_token,
        apple_public_key,
        issuer=CFG.APPLE_ISSUER,
        audience=CFG.MOBILE_APP_ID,
        algorithms=CFG.APPLE_DECODE_ALGORITHMS,
    )

    log(log.INFO, "Apple token verified, response: %s", decoded_token_raw)

    decoded_token = s.AppleTokenVerification.model_validate(decoded_token_raw)
    return decoded_token


def get_apple_fullname(decoded_token: s.AppleTokenVerification) -> str:
    if not decoded_token.fullName:
        return decoded_token.email.split("@")[0]
    if not decoded_token.fullName.givenName and not decoded_token.fullName.familyName:
        return decoded_token.email
    return f"{decoded_token.fullName.givenName} {decoded_token.fullName.familyName}".strip()
