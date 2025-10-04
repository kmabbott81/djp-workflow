# Authentication Setup

This guide covers setting up authentication for the DJP Workflow Platform to control access to your cloud deployment.

## Overview

The platform supports three authentication approaches:

1. **Cloud-native** - AWS Cognito / GCP IAP
2. **Cloudflare Access** - Zero Trust with any identity provider
3. **Reverse Proxy** - nginx/Caddy with OAuth2 Proxy

## AWS Authentication

### Option 1: ALB + Cognito

Use an Application Load Balancer with Amazon Cognito for user authentication.

**1. Create Cognito User Pool:**

```bash
aws cognito-idp create-user-pool \
  --pool-name djp-users \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 12,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true
    }
  }' \
  --auto-verified-attributes email \
  --region us-east-1
```

**2. Create User Pool Client:**

```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id us-east-1_XXXXXXXXX \
  --client-name djp-app-client \
  --generate-secret \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes openid email profile \
  --callback-urls https://djp.example.com/oauth2/idpresponse \
  --supported-identity-providers COGNITO
```

**3. Create User Pool Domain:**

```bash
aws cognito-idp create-user-pool-domain \
  --domain djp-auth \
  --user-pool-id us-east-1_XXXXXXXXX
```

**4. Configure ALB Authentication:**

```bash
# Create ALB listener rule with authentication
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --priority 1 \
  --conditions Field=path-pattern,Values='/*' \
  --actions '[
    {
      "Type": "authenticate-cognito",
      "Order": 1,
      "AuthenticateCognitoConfig": {
        "UserPoolArn": "arn:aws:cognito-idp:us-east-1:...:userpool/us-east-1_XXXXXXXXX",
        "UserPoolClientId": "xxxxxxxxxxxxxxxxxxxxx",
        "UserPoolDomain": "djp-auth",
        "OnUnauthenticatedRequest": "authenticate"
      }
    },
    {
      "Type": "forward",
      "Order": 2,
      "TargetGroupArn": "arn:aws:elasticloadbalancing:..."
    }
  ]'
```

**5. Add Users:**

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username john@example.com \
  --user-attributes Name=email,Value=john@example.com \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username john@example.com \
  --password "SecurePassword123!" \
  --permanent
```

### Option 2: ALB + OIDC (Okta/Auth0)

Use an external OIDC provider for SSO.

**1. Register application in your identity provider:**

- **Redirect URI**: `https://djp.example.com/oauth2/idpresponse`
- **Scopes**: `openid`, `email`, `profile`
- Note the **Client ID**, **Client Secret**, and **Issuer URL**

**2. Configure ALB listener rule:**

```bash
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --priority 1 \
  --conditions Field=path-pattern,Values='/*' \
  --actions '[
    {
      "Type": "authenticate-oidc",
      "Order": 1,
      "AuthenticateOidcConfig": {
        "Issuer": "https://your-domain.okta.com",
        "AuthorizationEndpoint": "https://your-domain.okta.com/oauth2/v1/authorize",
        "TokenEndpoint": "https://your-domain.okta.com/oauth2/v1/token",
        "UserInfoEndpoint": "https://your-domain.okta.com/oauth2/v1/userinfo",
        "ClientId": "xxxxxxxxxxxxx",
        "ClientSecret": "yyyyyyyyyyyyyyyy",
        "OnUnauthenticatedRequest": "authenticate"
      }
    },
    {
      "Type": "forward",
      "Order": 2,
      "TargetGroupArn": "arn:aws:elasticloadbalancing:..."
    }
  ]'
```

## GCP Authentication

### Cloud Run + IAP (Identity-Aware Proxy)

IAP provides zero-trust access control for Cloud Run services.

**1. Enable IAP API:**

```bash
gcloud services enable iap.googleapis.com
```

**2. Create OAuth consent screen:**

```bash
# This must be done in GCP Console
# Navigate to: APIs & Services > OAuth consent screen
# Configure app name, support email, and authorized domains
```

**3. Create OAuth Client:**

```bash
# Get this from GCP Console > APIs & Services > Credentials
# Create OAuth 2.0 Client ID > Web application
# Add authorized redirect URI: https://djp.example.com/_gcp_gatekeeper/authenticate
```

**4. Deploy Cloud Run with IAP:**

```bash
# Deploy service (requires authentication)
gcloud run deploy djp-workflow \
  --image us-central1-docker.pkg.dev/my-project/djp-workflow/app:latest \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated

# Enable IAP
gcloud beta run services add-iam-policy-binding djp-workflow \
  --region us-central1 \
  --member user:john@example.com \
  --role roles/run.invoker
```

**5. Configure custom domain with Load Balancer + IAP:**

```bash
# Create serverless NEG
gcloud compute network-endpoint-groups create djp-neg \
  --region us-central1 \
  --network-endpoint-type serverless \
  --cloud-run-service djp-workflow

# Create backend service
gcloud compute backend-services create djp-backend \
  --global \
  --load-balancing-scheme EXTERNAL_MANAGED

# Add NEG to backend
gcloud compute backend-services add-backend djp-backend \
  --global \
  --network-endpoint-group djp-neg \
  --network-endpoint-group-region us-central1

# Enable IAP on backend service
gcloud iap web enable \
  --resource-type backend-services \
  --oauth2-client-id xxxxx.apps.googleusercontent.com \
  --oauth2-client-secret yyyyyyyyyyyy \
  --service djp-backend

# Add IAM policy for access
gcloud iap web add-iam-policy-binding \
  --resource-type backend-services \
  --service djp-backend \
  --member user:john@example.com \
  --role roles/iap.httpsResourceAccessor
```

## Cloudflare Access

Cloudflare Access provides zero-trust authentication with any identity provider.

**1. Prerequisites:**

- Domain managed by Cloudflare
- Cloudflare Access enabled (available on Pro plans and above)

**2. Add Application:**

Navigate to **Zero Trust > Access > Applications** and click **Add an application**.

**Configuration:**
- **Name**: DJP Workflow
- **Subdomain**: `djp`
- **Domain**: `example.com`
- **Application type**: Self-hosted

**3. Configure Identity Provider:**

Navigate to **Settings > Authentication** and add a login method:

- **One-time PIN** (email-based, no setup required)
- **Google/GitHub/Okta** (OAuth)
- **SAML** (Enterprise SSO)

**4. Create Access Policy:**

Add a policy to control who can access:

```yaml
Policy Name: Team Members
Action: Allow
Include:
  - Emails: john@example.com, jane@example.com
  - Email domain: example.com
Exclude: []
Require:
  - Authentication method: Google
```

**5. Deploy Application:**

Point your application to Cloudflare:

```bash
# Update DNS to point to your origin (AWS/GCP)
# Cloudflare will automatically proxy and enforce authentication
```

**6. Application Settings:**

- **Session duration**: 24 hours (recommended)
- **Enable HTTP-only cookie**: ✓
- **Enable Same-Site cookie**: Strict
- **CORS**: Allow if needed for API access

**7. Verify:**

```bash
# Without authentication
curl https://djp.example.com
# Returns Cloudflare Access login page

# After authentication
# Browser automatically includes auth cookie
```

## OAuth2 Proxy

Use OAuth2 Proxy as a reverse proxy for any cloud deployment.

**1. Install OAuth2 Proxy:**

```bash
# Docker
docker pull quay.io/oauth2-proxy/oauth2-proxy:latest

# Binary
wget https://github.com/oauth2-proxy/oauth2-proxy/releases/download/v7.5.0/oauth2-proxy-v7.5.0.linux-amd64.tar.gz
tar -xvf oauth2-proxy-v7.5.0.linux-amd64.tar.gz
```

**2. Configure:**

Create `oauth2-proxy.cfg`:

```ini
# OAuth provider (google, github, okta, etc.)
provider = "google"
client_id = "xxxxx.apps.googleusercontent.com"
client_secret = "yyyyyyyyyyyy"

# Endpoints
redirect_url = "https://djp.example.com/oauth2/callback"
oidc_issuer_url = "https://accounts.google.com"

# Upstream application
http_address = "0.0.0.0:4180"
upstreams = ["http://localhost:8080"]

# Cookie settings
cookie_secret = "GENERATE_WITH_openssl_rand_base64_32"
cookie_secure = true
cookie_httponly = true

# Email restrictions
email_domains = ["example.com"]
# OR specific emails
# authenticated_emails_file = "/path/to/emails.txt"

# Logging
request_logging = true
auth_logging = true
```

**3. Generate cookie secret:**

```bash
openssl rand -base64 32
```

**4. Run OAuth2 Proxy:**

```bash
# Docker
docker run -d \
  -p 4180:4180 \
  -v $(pwd)/oauth2-proxy.cfg:/etc/oauth2-proxy.cfg \
  quay.io/oauth2-proxy/oauth2-proxy:latest \
  --config /etc/oauth2-proxy.cfg

# Binary
./oauth2-proxy --config oauth2-proxy.cfg
```

**5. Configure nginx reverse proxy:**

```nginx
server {
    listen 443 ssl http2;
    server_name djp.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /oauth2/ {
        proxy_pass http://127.0.0.1:4180;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Auth-Request-Redirect $request_uri;
    }

    location = /oauth2/auth {
        proxy_pass http://127.0.0.1:4180;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header Content-Length "";
        proxy_pass_request_body off;
    }

    location / {
        auth_request /oauth2/auth;
        error_page 401 = /oauth2/sign_in;

        # Pass auth headers to upstream
        auth_request_set $user $upstream_http_x_auth_request_user;
        auth_request_set $email $upstream_http_x_auth_request_email;
        proxy_set_header X-User $user;
        proxy_set_header X-Email $email;

        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Testing Authentication

### Test Unauthenticated Access

```bash
# Should redirect to login or return 401
curl -v https://djp.example.com

# Expected: 302 redirect or 401 Unauthorized
```

### Test Authenticated Access

```bash
# AWS Cognito - Get token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id xxxxx \
  --auth-parameters USERNAME=user@example.com,PASSWORD=password

# Use token in Authorization header
curl -H "Authorization: Bearer <id_token>" https://djp.example.com
```

### Test IAM/OIDC Claims

After authentication, check that user info is available:

```python
# In your application, check headers
import streamlit as st

# AWS ALB injects headers
user_claims = st.context.headers.get("x-amzn-oidc-data", "")

# GCP IAP injects headers
user_email = st.context.headers.get("x-goog-authenticated-user-email", "")

# OAuth2 Proxy injects headers
user_email = st.context.headers.get("x-email", "")
```

## Security Best Practices

1. **Use HTTPS only** - Never serve authentication over HTTP
2. **Rotate secrets** - Rotate OAuth client secrets every 90 days
3. **Session timeouts** - Set reasonable session durations (8-24 hours)
4. **MFA enforcement** - Enable MFA in your identity provider
5. **Audit logs** - Enable access logging for compliance
6. **Principle of least privilege** - Only grant access to users who need it
7. **Rate limiting** - Protect login endpoints from brute force attacks

## Troubleshooting

### Redirect Loop

- Check redirect URI matches exactly (trailing slash matters)
- Verify cookie domain settings
- Clear browser cookies and try again

### 401 Unauthorized After Login

- Check token expiration
- Verify IAM permissions (AWS) or IAP policy (GCP)
- Check OAuth scopes include required claims

### CORS Errors

- Add your domain to allowed origins in OAuth client
- Configure CORS headers in ALB/Cloud Run
- Use same-site cookie attribute appropriately

## Cost Considerations

| Solution | Cost |
|----------|------|
| AWS Cognito | Free tier: 50,000 MAUs, then $0.0055/MAU |
| GCP IAP | Free (included with Cloud Run) |
| Cloudflare Access | $3/user/month (Pro plan required) |
| OAuth2 Proxy | Free (self-hosted) |

## Next Steps

1. Choose authentication method based on your infrastructure
2. Configure identity provider (Cognito, Google, Okta, etc.)
3. Test authentication flow end-to-end
4. Enable MFA for all users
5. Set up monitoring and alerting for auth failures
6. Document user onboarding process
