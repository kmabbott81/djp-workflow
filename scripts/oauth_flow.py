"""Interactive OAuth flow helper for E2E testing.

This script guides you through the OAuth flow step-by-step.
"""

import webbrowser

import requests

print("=" * 70)
print("Google OAuth Flow - E2E Testing")
print("=" * 70)
print()

# Step 1: Get authorization URL
print("[Step 1/4] Fetching authorization URL from server...")
try:
    response = requests.get(
        "http://localhost:8003/oauth/google/authorize",
        params={"workspace_id": "test-workspace-e2e", "redirect_uri": "http://localhost:8003/oauth/google/callback"},
        timeout=5,
    )
    response.raise_for_status()
    auth_data = response.json()

    authorize_url = auth_data["authorize_url"]
    state = auth_data["state"]

    print("[OK] Authorization URL generated")
    print(f"     State: {state[:20]}...")
    print()
except Exception as e:
    print(f"[ERROR] Failed to fetch authorization URL: {e}")
    exit(1)

# Step 2: Open browser
print("[Step 2/4] Opening Google OAuth page in your browser...")
print()
print("           IMPORTANT: After you approve, Google will redirect to:")
print("           http://localhost:8003/oauth/google/callback")
print()
print("           You should see a JSON response like:")
print('           {"success": true, "scopes": "...", "has_refresh_token": true}')
print()
print("           Copy the ENTIRE JSON response and paste it here.")
print()

try:
    webbrowser.open(authorize_url)
    print("[OK] Browser opened. Please complete the OAuth flow:")
    print("     1. Sign in with kbmabb@gmail.com")
    print("     2. Click 'Continue' on unverified app warning")
    print("     3. Grant 'Send email' permission")
    print("     4. Copy the JSON response from the redirected page")
    print()
except Exception as e:
    print(f"[WARN] Could not open browser automatically: {e}")
    print()
    print("Please manually open this URL:")
    print(authorize_url)
    print()

# Step 3: Wait for user to complete flow
print("-" * 70)
print("[Step 3/4] Waiting for OAuth callback response...")
print()
callback_response = input("Paste the JSON response here (or press Enter to verify manually): ").strip()
print()

if callback_response:
    try:
        import json

        callback_data = json.loads(callback_response)

        if callback_data.get("success"):
            print("[OK] OAuth tokens stored successfully!")
            print(f"     Scopes: {callback_data.get('scopes', 'N/A')}")
            print(f"     Has refresh token: {callback_data.get('has_refresh_token', False)}")
        else:
            print("[ERROR] OAuth flow failed:")
            print(f"        {callback_data}")
    except json.JSONDecodeError:
        print("[WARN] Could not parse response as JSON")
        print("       Manual verification needed (step 4)")
else:
    print("[INFO] Skipping automatic verification")

print()

# Step 4: Verify tokens
print("[Step 4/4] Verifying OAuth tokens in database...")
print()

try:
    # Check token status endpoint
    response = requests.get(
        "http://localhost:8003/oauth/google/status", params={"workspace_id": "test-workspace-e2e"}, timeout=5
    )
    response.raise_for_status()
    status_data = response.json()

    if status_data.get("linked"):
        print("[OK] OAuth tokens found in database!")
        print(f"     Scopes: {status_data.get('scopes', 'N/A')}")
        print()
        print("=" * 70)
        print("SUCCESS! OAuth flow completed.")
        print("You can now run E2E tests with:")
        print("    python scripts/e2e_gmail_test.py --scenarios all --verbose")
        print("=" * 70)
    else:
        print("[ERROR] No OAuth tokens found in database")
        print("        The OAuth flow may have failed silently.")
        print()
        print("        Please check server logs:")
        print("        - Look for ERROR or Traceback in the uvicorn output")
        print("        - Verify REDIS_URL and DATABASE_URL are set correctly")

except Exception as e:
    print(f"[ERROR] Failed to verify tokens: {e}")
    print()
    print("        Manual verification command:")
    print("        curl 'http://localhost:8003/oauth/google/status?workspace_id=test-workspace-e2e'")

print()
