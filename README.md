# ParcelTrack

## Setup

Install the dependencies, set a secret key in the environment, then apply the migrations:

```bash
pip install -r requirements.txt
export DJANGO_SECRET_KEY="your-secret-key"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

On Windows PowerShell, set the key with `$env:DJANGO_SECRET_KEY = "your-secret-key"`.
The Django superuser can sign in at `/admin/`; set that account's ParcelTrack role to
`admin` there. Set `DJANGO_HTTPS=true` when serving over HTTPS to enable secure session
cookies. The security logger writes authentication events to `security.log`.

Registration is at `/accounts/register/`, login at `/accounts/login/`, and logout is a
CSRF-protected POST action. Run `python manage.py makemigrations` when changing models.
