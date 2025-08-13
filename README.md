# Chat My History

A Flask web app that guides seniors through voice/text interviews to capture a rich personal history, with admin controls, LLM integrations, and export-ready structure.

## Features
- Guided interview chat with adaptive follow-ups (OpenAI/Anthropic/Google)
- User accounts with admin role
- Manage LLM system prompts (admin)
- Store interviews, messages, and media
- WSGI entry for Apache deployment

## Quickstart (Dev)
1. Python 3.11+
2. Create virtualenv and install deps:
   ```bash
   python -m venv .venv && . .venv/Scripts/activate  # Windows PowerShell
   pip install -r requirements.txt
   ```
3. Copy `.env-example` to `.env` and fill values. Set `OPENAI_API_KEY` (or Anthropic/Google) and MySQL creds.
4. Build CSS (Tailwind):
   ```bash
   npm i -D tailwindcss
   npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch
   ```
5. Run app:
   ```bash
   python run.py
   ```

## MySQL
Create database and user:
```sql
CREATE DATABASE chatmyhistory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON chatmyhistory.* TO 'chat_user'@'localhost';
FLUSH PRIVILEGES;
```

## Apache (Ubuntu) with mod_wsgi
- Ensure packages: `sudo apt install apache2 libapache2-mod-wsgi-py3`
- Project path: `/var/www/chatmyhistory`
- WSGI file: `wsgi.py` (exposes `application`)
- Example vhost:
```
<VirtualHost *:80>
    ServerName your.domain
    ServerAdmin admin@your.domain

    WSGIDaemonProcess chatmyhistory python-home=/var/www/chatmyhistory/.venv python-path=/var/www/chatmyhistory
    WSGIScriptAlias / /var/www/chatmyhistory/wsgi.py

    <Directory /var/www/chatmyhistory>
        Require all granted
    </Directory>

    Alias /static/ /var/www/chatmyhistory/app/static/
    <Directory /var/www/chatmyhistory/app/static>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/chatmyhistory-error.log
    CustomLog ${APACHE_LOG_DIR}/chatmyhistory-access.log combined
</VirtualHost>
```
- Reload: `sudo a2enmod wsgi && sudo systemctl reload apache2`

## Environment
- `LLM_PROVIDER`: `openai|anthropic|google`
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- `SQLALCHEMY_DATABASE_URI` for MySQL

## Notes
- This is a foundation; voice recording, transcription, exports, and advanced media tools can be added next.
- Accessibility: large controls, high contrast, minimal steps.
