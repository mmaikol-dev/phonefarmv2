# STF Token Setup And Troubleshooting

## Issue

The Laravel dashboard needed a valid STF API token in order to call:

```text
GET /api/v1/devices
```

The token that was in `.env`:

```env
STF_TOKEN=phonefarm-token-001
```

was not valid.

When tested with `curl`, STF returned:

```json
{"success":false,"description":"Bad Credentials"}
```

## Root Cause

There were two separate problems:

1. The token in `.env` was only a placeholder and not a real STF access token.
2. The normal STF account page flow was not available in this local setup, so token generation had to be done through the mock-auth plus session flow.

There was also a temporary authentication issue caused by mixing:

- `localhost`
- `127.0.0.1`

Cookies created for one host were not valid for the other host, so the STF session was not being recognized.

## What We Did

We restarted the token-generation flow from scratch and used `127.0.0.1` consistently for every request.

The working process was:

1. Remove old cookie and login files.
2. Fetch the STF mock login page and save cookies.
3. Read the `XSRF-TOKEN` from the cookie file.
4. Log in to STF mock auth with the CSRF header.
5. Follow the returned `jwt` redirect URL to establish the STF session.
6. Confirm the session was authenticated with `/api/v1/user`.
7. Create a new STF access token.
8. Verify the new token with `/api/v1/devices`.

## Commands Used

### 1. Clean old STF cookie files

```bash
rm -f stf-cookies.txt stf-login.html
```

### 2. Get fresh login page and cookies

```bash
curl -s http://127.0.0.1:7100/auth/mock -c stf-cookies.txt -o stf-login.html
```

### 3. Inspect the cookie file

```bash
cat stf-cookies.txt
```

This gave an `XSRF-TOKEN` value that was then used in the next command.

### 4. Log in through STF mock auth

```bash
curl -s -X POST http://127.0.0.1:7100/auth/api/v1/mock \
  -b stf-cookies.txt -c stf-cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-XSRF-TOKEN: <XSRF_TOKEN_FROM_COOKIE_FILE>" \
  -d '{"email":"admin@phonefarm.local","name":"PhoneFarm"}'
```

This returned JSON with a `redirect` URL like:

```json
{
  "success": true,
  "redirect": "http://127.0.0.1:7100/?jwt=..."
}
```

### 5. Follow the STF JWT redirect and establish the session

```bash
curl -i -L "http://127.0.0.1:7100/?jwt=<JWT_FROM_REDIRECT>" \
  -b stf-cookies.txt -c stf-cookies.txt
```

### 6. Confirm STF session authentication

```bash
curl -s http://127.0.0.1:7100/api/v1/user \
  -b stf-cookies.txt
```

This returned authenticated user JSON, confirming the session was valid.

### 7. Create a new STF access token

```bash
curl -s -X POST "http://127.0.0.1:7100/api/v1/user/accessTokens?title=phonefarm-laravel" \
  -b stf-cookies.txt
```

This returned:

```json
{
  "success": true,
  "description": "Created (access token)",
  "token": {
    "id": "<NEW_STF_TOKEN>",
    "title": "phonefarm-laravel"
  }
}
```

Important:

- `token.id` is the value that must be used as the bearer token.

### 8. Verify the new token

```bash
curl -s http://127.0.0.1:7100/api/v1/devices \
  -H "Authorization: Bearer <NEW_STF_TOKEN>"
```

This returned a successful STF device response, which confirmed the token was valid.

## Laravel `.env` Update

The project should use:

```env
STF_BASE_URL=http://127.0.0.1:7100
STF_TOKEN=<NEW_STF_TOKEN>
```

After updating `.env`, clear Laravel config:

```bash
cd /home/atlas/PHONE\ FARM/phonefarmv2
php artisan config:clear
```

## Result

The STF token generation process worked, and the new token successfully authenticated against:

```text
http://127.0.0.1:7100/api/v1/devices
```

## Extra Note

During verification, STF returned device data successfully, but the device state showed:

- `present: false`
- `ready: false`

So token authentication is fixed, but if the dashboard still shows no active phone, the next issue to troubleshoot is device availability inside STF rather than authentication.
