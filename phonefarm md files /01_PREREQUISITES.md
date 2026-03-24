# ✅ Step 01 — Prerequisites

## Install PHP 8.2

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:ondrej/php -y
sudo apt update
sudo apt install -y php8.2 php8.2-cli php8.2-curl php8.2-mbstring php8.2-xml php8.2-zip
```

Verify:
```bash
php --version
# Should show PHP 8.2.x
```

---

## Install Composer

```bash
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
composer --version
```

---

## Verify STF Is Running

Open a terminal and run:
```bash
docker start rethinkdb
nvm use 18
stf local --public-ip 127.0.0.1
```

Open browser → `http://localhost:7100`
You should see the STF interface.

---

## Verify Phone Is Connected

```bash
adb devices
```

Should show your phone:
```
List of devices attached
aece3bbd    device
```

---

## Checklist Before Moving On

- [ ] `php --version` shows 8.2+
- [ ] `composer --version` works
- [ ] STF running at http://localhost:7100
- [ ] Phone showing in STF interface
- [ ] `adb devices` shows phone
