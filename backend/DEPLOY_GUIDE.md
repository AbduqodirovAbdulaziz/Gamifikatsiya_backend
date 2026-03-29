# EduGame Backend - Server Deploy Qo'llanmasi

## 📋 Mundarija

1. [Server Talablari](#server-talablari)
2. [Ubuntu 22.04 da O'rnatish](#ubuntu-2204-da-or-natish)
3. [Django Konfiguratsiya](#django-konfiguratsiya)
4. [Nginx Sozlash](#nginx-sozlash)
5. [Gunicorn + Daphne](#gunicorn--daphne)
6. [SSL Sertifikat](#ssl-sertifikat)
7. [Systemd Service](#systemd-service)
8. [Git Deploy](#git-deploy)

---

## Server Talablari

### Minimal:
- 1 GB RAM
- 20 GB SSD
- Ubuntu 22.04 LTS
- Python 3.12+

### Tavsiya etilgan:
- 2 GB RAM
- 40 GB SSD
- Ubuntu 22.04 LTS
- Python 3.12+

---

## Ubuntu 22.04 da O'rnatish

### 1. Sistemani yangilash

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Python va kerakli paketlar

```bash
# Python o'rnatish
sudo apt install python3.12 python3.12-venv python3-pip -y

# Sistemaviy kutubxonalar
sudo apt install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    ffmpeg \
    git \
    curl \
    wget
```

### 3. PostgreSQL o'rnatish

```bash
# PostgreSQL repo qo'shish
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# PostgreSQL o'rnatish
sudo apt install -y postgresql-16 postgresql-contrib-16

# PostgreSQL servisi
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 4. Redis o'rnatish

```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 5. Nginx o'rnatish

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

---

## PostgreSQL Ma'lumotlar Bazasini Yaratish

```bash
# PostgreSQL ga ulanish
sudo -u postgres psql

# Create database and user
CREATE DATABASE edugame_db;
CREATE USER edugame_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE edugame_db TO edugame_user;

# Exit
\q
```

```bash
# Encoding sozlamasi
sudo -u postgres psql -d edugame_db -c "ALTER DATABASE edugame_db SET client_encoding TO 'UTF8';"
```

---

## Django Konfiguratsiya

### 1. Loyihani yuklab olish

```bash
# /var/www papkasini yaratish
sudo mkdir -p /var/www
cd /var/www

# Git dan clone (yoki SCP bilan yuklab olish)
sudo git clone https://github.com/YOUR_USERNAME/edugame.git
cd edugame/backend

# Yoki papka nomini o'zgartirish
sudo mv edugame edugame_backend
cd edugame_backend
```

### 2. Virtual Environment yaratish

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Paketlarni o'rnatish

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. .env faylini yaratish

```bash
sudo nano /var/www/edugame_backend/.env
```

```env
# Django
SECRET_KEY=YOUR_SUPER_SECRET_KEY_MIN_50_CHARS
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server-ip

# Database
DATABASE_URL=postgres://edugame_user:STRONG_PASSWORD_HERE@localhost:5432/edugame_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.production

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

```bash
chmod 600 /var/www/edugame_backend/.env
```

### 5. Migration va Static Files

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6. Papka huquqlari

```bash
sudo chown -R www-data:www-data /var/www/edugame_backend
sudo chmod -R 755 /var/www/edugame_backend
sudo mkdir -p /var/www/edugame_backend/media
sudo chown -R www-data:www-data /var/www/edugame_backend/media
```

---

## Nginx Sozlash

### 1. Nginx konfiguratsiya fayli

```bash
sudo nano /etc/nginx/sites-available/edugame
```

```nginx
# HTTP - HTTPS ga redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    return 301 https://$server_name$request_uri;
}

# HTTPS konfiguratsiya
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Sertifikat (Certbot dan keyin avtomatik)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Root papka
    root /var/www/edugame_backend;

    # Static fayllar
    location /static/ {
        alias /var/www/edugame_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media fayllar
    location /media/ {
        alias /var/www/edugame_backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API proxypass
    location /api/ {
        proxy_pass http://unix:/var/www/edugame_backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket uchun
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Admin static fayllar
    location /static/admin/ {
        alias /var/www/edugame_backend/staticfiles/admin/;
        expires 30d;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://unix:/var/www/edugame_backend/daphne.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # Frontend ga redirect (agar alohida serving qilish kerak bo'lsa)
    # location / {
    #     proxy_pass http://localhost:3000;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Real-IP $remote_addr;
    # }
}
```

```bash
# Nginx ni yoqish
sudo ln -s /etc/nginx/sites-available/edugame /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Default ni o'chirish
sudo nginx -t  # Tekshirish
sudo systemctl reload nginx
```

---

## Gunicorn + Daphne

### 1. Gunicorn konfiguratsiya

```bash
sudo nano /var/www/edugame_backend/gunicorn_config.py
```

```python
import multiprocessing

# Bind
bind = "unix:/var/www/edugame_backend/gunicorn.sock"

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/www/edugame_backend/logs/gunicorn_access.log"
errorlog = "/var/www/edugame_backend/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "edugame_api"

# Daemon
daemon = False

# User/Group
user = "www-data"
group = "www-data"

# Python path
pythonpath = "/var/www/edugame_backend"
chdir = "/var/www/edugame_backend"
```

```bash
# Log papkalar
sudo mkdir -p /var/www/edugame_backend/logs
sudo chown -R www-data:www-data /var/www/edugame_backend/logs
```

### 2. Daphne konfiguratsiya (WebSocket uchun)

```bash
sudo nano /var/www/edugame_backend/daphne_config.py
```

```python
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Application
application = 'config.asgi:application'

# Bind
bind = [
    'unix:/var/www/edugame_backend/daphne.sock',
]

# Workers
workers = 2

# Logging
access_log = '/var/www/edugame_backend/logs/daphne_access.log'
error_log = '/var/www/edugame_backend/logs/daphne_error.log'
log_level = 'info'

# Timeout
websocket_timeout = 86400
websocket_handshake_timeout = 60
```

---

## Systemd Service

### 1. Gunicorn Service

```bash
sudo nano /etc/systemd/system/edugame-gunicorn.service
```

```ini
[Unit]
Description=EduGame Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edugame_backend
Environment=PATH=/var/www/edugame_backend/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/var/www/edugame_backend
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/var/www/edugame_backend/venv/bin/gunicorn \
    --config /var/www/edugame_backend/gunicorn_config.py \
    config.asgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Daphne Service (WebSocket)

```bash
sudo nano /etc/systemd/system/edugame-daphne.service
```

```ini
[Unit]
Description=EduGame Daphne WebSocket Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edugame_backend
Environment=PATH=/var/www/edugame_backend/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/var/www/edugame_backend
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/var/www/edugame_backend/venv/bin/daphne \
    --bind 0.0.0.0:8001 \
    --access-log /var/www/edugame_backend/logs/daphne_access.log \
    --error-log /var/www/edugame_backend/logs/daphne_error.log \
    config.asgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Celery Service

```bash
sudo nano /etc/systemd/system/edugame-celery.service
```

```ini
[Unit]
Description=EduGame Celery Worker
After=network.target redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edugame_backend
Environment=PATH=/var/www/edugame_backend/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/var/www/edugame_backend
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/var/www/edugame_backend/venv/bin/celery -A config worker --loglevel=info --logfile=/var/www/edugame_backend/logs/celery.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Celery Beat Service (Scheduler)

```bash
sudo nano /etc/systemd/system/edugame-celery-beat.service
```

```ini
[Unit]
Description=EduGame Celery Beat Scheduler
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edugame_backend
Environment=PATH=/var/www/edugame_backend/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/var/www/edugame_backend
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/var/www/edugame_backend/venv/bin/celery -A config beat --loglevel=info --logfile=/var/www/edugame_backend/logs/celery_beat.log --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Servicelarni yoqish

```bash
# Servicelarni yangilash
sudo systemctl daemon-reload

# Servicelarni yoqish
sudo systemctl enable edugame-gunicorn
sudo systemctl enable edugame-daphne
sudo systemctl enable edugame-celery
sudo systemctl enable edugame-celery-beat

# Servicelarni boshlash
sudo systemctl start edugame-gunicorn
sudo systemctl start edugame-daphne
sudo systemctl start edugame-celery
sudo systemctl start edugame-celery-beat

# Statusni tekshirish
sudo systemctl status edugame-gunicorn
sudo systemctl status edugame-daphne
```

---

## SSL Sertifikat (Let's Encrypt)

```bash
# Certbot
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal tekshirish
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## Git Deploy (Auto-Deploy)

### 1. Git Hook

```bash
# Deploy user yaratish (ixtiyoriy)
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG www-data deploy

# Hook papka
sudo mkdir -p /var/repo/edugame.git
cd /var/repo/edugame.git
sudo git init --bare

# Hook yaratish
sudo nano /var/repo/edugame.git/hooks/post-receive
```

```bash
#!/bin/bash

TARGET="/var/www/edugame_backend"
GIT_DIR="/var/repo/edugame.git"
BRANCH="main"

while read oldrev newrev refname; do
    branch=$(echo $refname | sed 's|refs/heads/||')
    
    if [ "$branch" == "$BRANCH" ]; then
        echo "Deploying $branch..."
        
        # Pull code
        GIT_WORK_TREE=$TARGET git checkout -f $BRANCH
        
        # Virtual env
        cd $TARGET
        source venv/bin/activate
        
        # Dependencies
        pip install -r requirements.txt
        
        # Migrate
        python manage.py migrate
        
        # Static files
        python manage.py collectstatic --noinput
        
        # Restart services
        sudo systemctl restart edugame-gunicorn
        sudo systemctl restart edugame-daphne
        sudo systemctl restart edugame-celery
        
        echo "Deployment complete!"
    fi
done
```

```bash
chmod +x /var/repo/edugame.git/hooks/post-receive
chown deploy:deploy /var/repo/edugame.git/hooks/post-receive
```

### 2. Local dan push qilish

```bash
# Local loyihada
git remote add production deploy@your-server:/var/repo/edugame.git

# Push
git push production main
```

---

## Tekshirish va Monitorlash

### Servicelar statusi

```bash
# Barcha servicelarni tekshirish
sudo systemctl status edugame-gunicorn edugame-daphne edugame-celery edugame-celery-beat

# Loglarni ko'rish
sudo journalctl -u edugame-gunicorn -f
sudo journalctl -u edugame-daphne -f
sudo tail -f /var/www/edugame_backend/logs/gunicorn_error.log
```

### API ni tekshirish

```bash
# Health check
curl -I https://yourdomain.com/api/v1/auth/login/

# WebSocket test
wscat -c wss://yourdomain.com/ws/notifications/USER_ID/
```

### Firewall

```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
sudo ufw status
```

---

## Muammolarni Hal Qilish

### 1. 502 Bad Gateway

```bash
# Socket mavjudligini tekshirish
ls -la /var/www/edugame_backend/*.sock

# Gunicorn log
tail -50 /var/www/edugame_backend/logs/gunicorn_error.log

# Serviceni qayta boshlash
sudo systemctl restart edugame-gunicorn
```

### 2. Database ulanish xatosi

```bash
# PostgreSQL status
sudo systemctl status postgresql

# Ulanishni tekshirish
sudo -u postgres psql -d edugame_db -c "SELECT 1;"

# .env DATABASE_URL tekshirish
cat /var/www/edugame_backend/.env | grep DATABASE
```

### 3. Static fayllar ko'rinmaydi

```bash
# Static papka
ls -la /var/www/edugame_backend/staticfiles/

# Collectstatic
source venv/bin/activate
python manage.py collectstatic --clear --noinput

# Nginx ni qayta yuklash
sudo systemctl reload nginx
```

### 4. WebSocket ishlameyapti

```bash
# Daphne status
sudo systemctl status edugame-daphne

# Socket tekshirish
ls -la /var/www/edugame_backend/daphne.sock

# Daphne log
tail -50 /var/www/edugame_backend/logs/daphne_error.log
```

---

## Tez-tez Buyruqlar

```bash
# Servicelarni boshqarish
sudo systemctl start edugame-gunicorn
sudo systemctl stop edugame-gunicorn
sudo systemctl restart edugame-gunicorn

# Logs
sudo journalctl -u edugame-gunicorn --since "1 hour ago"
sudo tail -f /var/www/edugame_backend/logs/gunicorn_error.log

# Deploy
cd /var/www/edugame_backend
source venv/bin/activate
git pull
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart edugame-gunicorn edugame-daphne edugame-celery

# Backup
pg_dump edugame_db > backup_$(date +%Y%m%d).sql

# SSL yangilash
sudo certbot renew
```

---

## Xavfsizlik

### 1. Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Xavfsizlik yangilanishlari

```bash
# Auto-update
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Alohida Frontend Deploy

Agar Next.js frontend alohida serverda bo'lsa:

```nginx
# /etc/nginx/sites-available/edugame-frontend

server {
    listen 80;
    server_name frontend.yourdomain.com;
    
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name frontend.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    root /var/www/edugame-frontend/.next;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /_next/static {
        alias /var/www/edugame-frontend/.next/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Contact & Support

Muammolar bo'lsa, loglarni tekshiring:
```bash
sudo journalctl -xe
```

Yoki server loglarini ko'ring:
```bash
tail -100 /var/www/edugame_backend/logs/gunicorn_error.log
```
