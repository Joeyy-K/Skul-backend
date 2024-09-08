import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skul.settings")
django.setup()

from school.models import User

def generate_avatars():
    users = User.objects.all()
    for user in users:
        user.generate_avatar()
        user.save()
        print(f'Generated avatar for {user.username}')

if __name__ == "__main__":
    generate_avatars()