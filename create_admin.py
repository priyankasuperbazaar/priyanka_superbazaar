from django.contrib.auth.models import User

username = "priyanka_superbazaar"
password = "priyanka@rahul2025"
email = "admin@example.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")