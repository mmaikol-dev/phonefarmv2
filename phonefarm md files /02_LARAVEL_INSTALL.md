# 🛠️ Step 02 — Create the Laravel Project

## Create New Laravel App

```bash
cd ~
composer create-project laravel/laravel phonefarm
cd phonefarm
```

This creates a folder called `phonefarm` with a fresh Laravel app.

---

## Start Laravel Dev Server

```bash
php artisan serve
```

Open browser → `http://localhost:8000`

You should see the default Laravel welcome page. ✅

---

## Set Up Environment File

Open the `.env` file in the phonefarm folder:
```bash
nano .env
```

Find these lines and update them:
```env
APP_NAME=PhoneFarm
APP_URL=http://localhost:8000
```

Also add these two new lines at the bottom of the file:
```env
STF_BASE_URL=http://localhost:7100
STF_TOKEN=your_token_here
```

> Leave `STF_TOKEN` as `your_token_here` for now.
> We will fill it in Step 03.

Save the file: `Ctrl+X` then `Y` then `Enter`

---

## Folder Structure (What Matters)

```
phonefarm/
├── app/
│   ├── Http/
│   │   └── Controllers/
│   │       └── PhoneController.php   ← we will create this
│   └── Services/
│       └── STFService.php            ← we will create this
├── resources/
│   └──(use shadcn user uses laravel shadcn staterkit)          ← we will create this
├── routes/
│   └── web.php                       ← we will edit this
└── .env                              ← already edited above
```

---

## Checklist

- [ ] `composer create-project` ran successfully
- [ ] `php artisan serve` starts without errors
- [ ] Browser shows Laravel welcome page at localhost:8000
- [ ] `.env` updated with STF_BASE_URL and STF_TOKEN placeholder
