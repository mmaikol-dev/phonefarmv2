# 📱 Laravel Virtual Phone — Local Setup Guide

## Goal
One simple thing — display your Android phone screen
inside a Laravel page in the browser.

That's it. Nothing else in this guide.

---

## What You Will Have at the End

```
Browser opens http://localhost:8000
        ↓
Laravel page loads
        ↓
Your Redmi Note 10 Pro screen appears live
        ↓
You can tap and control it from the browser
```

---

## Files In This Guide

```
00_OVERVIEW.md          ← You are here
01_PREREQUISITES.md     ← PHP, Composer, MySQL
02_LARAVEL_INSTALL.md   ← Create the Laravel project
03_STF_TOKEN.md         ← Get STF API token
04_STF_SERVICE.md       ← Laravel class that talks to STF
05_ROUTE_AND_VIEW.md    ← The page that shows the phone
06_TESTING.md           ← Run it and see the phone
```

---

## Prerequisites
- [ ] STF running (`stf local --public-ip 127.0.0.1`)
- [ ] RethinkDB running (`docker start rethinkdb`)
- [ ] Phone connected (`adb devices` shows phone)
- [ ] PHP 8.2+
- [ ] Composer
