# 🔑 Step 03 — Get Your STF API Token

STF requires an access token to allow external apps (like Laravel) to call its API.

---

## Step 1 — Open STF

Make sure STF is running, then open:
```
http://localhost:7100
```

---

## Step 2 — Log In

On the STF login page enter any email:
```
admin@phonefarm.local
```
Click **"Sign in"** — in local mock mode any email works.

---

## Step 3 — Go to Your Account

Once logged in, click your email/avatar in the top right corner.
Then click **"Account"** or go directly to:
```
http://localhost:7100/#!/account
```

---

## Step 4 — Generate a Token

- Scroll down to **"Access Tokens"**
- Click the **"+"** button
- A token string appears — it looks like this:
```
9d2c4f1a8b3e7f6d0c5a2b9e4f1d8c3a
```
- **Copy it immediately** — you can only see it once

---

## Step 5 — Add Token to Laravel .env

Open your Laravel `.env` file:
```bash
cd ~/phonefarm
nano .env
```

Find this line:
```env
STF_TOKEN=your_token_here
```

Replace with your actual token:
```env
STF_TOKEN=9d2c4f1a8b3e7f6d0c5a2b9e4f1d8c3a
```

Save: `Ctrl+X` → `Y` → `Enter`

---

## Step 6 — Clear Laravel Config Cache

After changing `.env`, always run:
```bash
php artisan config:clear
```

---

## Verify the Token Works

Test your token directly in the terminal:
```bash
curl http://localhost:7100/api/v1/devices \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

You should get a JSON response like:
```json
{
  "devices": [
    {
      "serial": "aece3bbd",
      "present": true,
      "ready": true,
      "model": "Redmi Note 10 Pro",
      ...
    }
  ]
}
```

If you see your phone in the JSON — the token works. ✅

---

## Checklist

- [ ] Logged into STF at localhost:7100
- [ ] Generated access token
- [ ] Token added to `.env` file
- [ ] `php artisan config:clear` run
- [ ] `curl` test returns phone JSON
