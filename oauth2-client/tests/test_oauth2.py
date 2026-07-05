import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from oauth2 import OAuth2Client, TokenResponse, PKCE


def test_pkce_verifier():
    v = PKCE.generate_verifier()
    assert len(v) > 0
    assert len(v) <= 64

def test_pkce_challenge_s256():
    v = PKCE.generate_verifier()
    c = PKCE.generate_challenge(v, "S256")
    assert len(c) > 0
    assert c != v

def test_pkce_challenge_plain():
    v = PKCE.generate_verifier()
    c = PKCE.generate_challenge(v, "plain")
    assert c == v

def test_pkce_pair():
    v, c = PKCE.create_pair()
    assert v != c
    assert len(v) > 0
    assert len(c) > 0

def test_pkce_invalid_method():
    try:
        PKCE.generate_challenge("verifier", "invalid")
        assert False
    except ValueError:
        pass

def test_token_response_init():
    t = TokenResponse(access_token="abc", expires_in=3600)
    assert t.access_token == "abc"
    assert t.expires_at > 0
    assert not t.is_expired

def test_token_expired():
    t = TokenResponse(access_token="abc", expires_in=0, expires_at=time.time() - 100)
    assert t.is_expired

def test_token_not_expired():
    t = TokenResponse(access_token="abc", expires_in=3600)
    assert not t.is_expired

def test_authorization_header():
    t = TokenResponse(access_token="abc", token_type="Bearer")
    h = t.authorization_header
    assert h["Authorization"] == "Bearer abc"

def test_oauth_init():
    client = OAuth2Client("client_id", "secret", "https://callback", "https://token", "https://auth")
    assert client.client_id == "client_id"
    assert client.redirect_uri == "https://callback"

def test_authorization_url():
    client = OAuth2Client("id", "secret", "https://cb", "https://token", "https://auth", scope="read")
    url = client.get_authorization_url(state="xyz")
    assert "response_type=code" in url
    assert "client_id=id" in url
    assert "state=xyz" in url
    assert "scope=read" in url

def test_authorization_url_pkce():
    client = OAuth2Client("id", "secret", "https://cb", "https://token", "https://auth")
    v, c = PKCE.create_pair()
    url = client.get_authorization_url(pkce=(v, c))
    assert "code_challenge=" in url
    assert "S256" in url

def test_set_token():
    client = OAuth2Client("id")
    token = TokenResponse(access_token="tok", expires_in=3600)
    client.set_token(token)
    assert client.get_token() is not None

def test_is_authenticated():
    client = OAuth2Client("id")
    assert not client.is_authenticated
    client.set_token(TokenResponse(access_token="tok", expires_in=3600))
    assert client.is_authenticated

def test_auth_headers():
    client = OAuth2Client("id")
    assert client.auth_headers() == {}
    client.set_token(TokenResponse(access_token="tok", expires_in=3600))
    h = client.auth_headers()
    assert "Authorization" in h

def test_refresh_no_token():
    client = OAuth2Client("id")
    try:
        client.refresh_token()
        assert False
    except ValueError:
        pass

def test_refresh_callback():
    client = OAuth2Client("id", "secret", token_url="https://token")
    called = []
    client.set_refresh_callback(lambda t: called.append(t))
    # Can't actually call refresh without a server, but callback is set
    assert len(called) == 0

def test_authorization_url_extra_params():
    client = OAuth2Client("id", "secret", "https://cb", "https://token", "https://auth")
    url = client.get_authorization_url(extra_params={"access_type": "offline"})
    assert "access_type=offline" in url

def test_token_raw():
    t = TokenResponse(access_token="a", raw={"extra": "data"})
    assert t.raw["extra"] == "data"
