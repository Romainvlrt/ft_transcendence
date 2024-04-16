import requests
from Transcendance.models import User
from django.core.files.base import ContentFile


def get_info_from_42(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get("https://api.intra.42.fr/v2/me", headers=headers)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"request failed with status {response.status_code} and response {response.text}")
    return data



def register_user(access_token):
    data = get_info_from_42(access_token)

    if User.objects.filter(id_42=data['id']).exists():
        return User.objects.get(id_42=data['id'])
    else:
        user = User()
        user.id_42 = data['id']
        user.username = data['login']
        if User.objects.filter(username=data['login']).exists():
            user.username = data['login'] + str(data['id'])
        user.email = data['email']
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        
        response = requests.get(data['image']['link'])
        content_file = ContentFile(response.content)
        user.avatar.save(f"{user.username}.jpg", content_file)
        user.save()
    return user
