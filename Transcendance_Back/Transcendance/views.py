import os
import requests
from django.shortcuts import render, redirect
from .forms import AccountCreationForm, AccountLoginForm, RegularAccountUpdateForm, Auth42AccountUpdateForm
from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.hashers import make_password
from .models import Message, User, Conversation
from dotenv import load_dotenv
from django.http import HttpResponseRedirect
from urllib.parse import urlencode
from django.urls import reverse
from django.http import HttpResponse
from Transcendance.management.OAuth20.get_info_from_42 import register_user 
from django.shortcuts import get_object_or_404



def AccountCreation(request):
    if request.method == 'POST':
        form = AccountCreationForm(request.POST)
        if form.is_valid():
            try:
                form.Create_User(request)
                return redirect('hello')
            except forms.ValidationError as e:
                error = e
                return render(request, "Account_creation.html", {"form" : form})
    else:
        form = AccountCreationForm()
    return render(request, "Account_creation.html", {"form" : form})

def AccountLogin(request):
    if request.method == 'POST':
        form = AccountLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if form.Login(request):
                return redirect('hello')
    else:
        form = AccountLoginForm()
    return render(request, "Account_login.html", {"form" : form})

def Hello(request):
    return render(request, 'Hello.html')

def LoginPage(request):
    return render(request, 'Login_page.html')

def FailedLogin(request):
    return render(request, 'Failed_login.html')

def Logout(request):
    user = request.user
    logout(request)
    return redirect('hello')

def ChatView(request):
    if Conversation.objects.all().count() == 0:
        conversation = Conversation(conversation="General")
        conversation.save()
    try:
        conversation = Conversation.objects.get(conversation="General")
        message_backup = conversation.messages.all().order_by('timestamp')
    except Conversation.DoesNotExist:
        message_backup = None
    return render(request, "Chat_room.html", {'message': message_backup})

def PrivateChatView(request, room_name):
    Sortroom_name = room_name.split('_')
    Sortroom_name.sort()
    room_name = "_".join(Sortroom_name)
    if Conversation.objects.filter(conversation=room_name).count() == 0:
        conversation = Conversation(conversation=room_name)
        conversation.save()
    try:
        conversation = Conversation.objects.get(conversation=room_name)
        message_backup = conversation.messages.all().order_by('timestamp')
    except Conversation.DoesNotExist:
        message_backup = None

    usernames = room_name.split('_')
    if request.user.username not in usernames:
        return redirect('hello')
    return render(request, "Private_chatroom.html", {'message': message_backup})



    return render(request, "Private_chat_room.html", {'message': message_backup, 'usernames': usernames})

def redirect_to_provider(request):
    load_dotenv()
    base_url = "https://api.intra.42.fr/oauth/authorize"
    params = {
        "client_id": os.getenv("CLIENT_ID"),
        "redirect_uri": 'https://localhost:/callback',
        "response_type": "code",
    }
    auth_url = f"{base_url}?{urlencode(params)}"
    return HttpResponseRedirect(auth_url)

def callback_view(request):
    load_dotenv()
    code = request.GET.get("code")
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://localhost:/callback',
        'client_id': os.getenv("CLIENT_ID"),
        'client_secret': os.getenv("CLIENT_SECRET"),
    }
    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    error = request.GET.get("error")
    response_data = response.json()
    if error or not 'access_token' in response_data:
        return HttpResponse(f"Failed to authenticate with 42: {error}\n{response_data}", status=400)
    else:
        access_token = response_data['access_token']
        user = register_user(access_token)
        login(request, user)
    return redirect('hello')

def AccountUpdate(request):
    user = User.objects.get(username=request.user.username)
    if request.method == 'POST':
        if user.id_42:
            form = Auth42AccountUpdateForm(request.POST, request.FILES, instance=user)
        else:
            form = RegularAccountUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            username = form.cleaned_data.get('email')
            password = form.cleaned_data.get('new_password')
            form.save()
            if username:
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
            elif password:
                update_session_auth_hash(request, user)
            return redirect('hello')
    else:
        if user.id_42:
            form = Auth42AccountUpdateForm(initial={
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }, instance=user)
        else:
            form = RegularAccountUpdateForm(initial={
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': ""
            }, instance=user)
    return render(request, 'Update_account.html', {'form': form})

def PFC_view(request, room_name):
    users = room_name.split('_')
    if request.user.username not in users:
        return redirect('hello')
    return render(request, 'PFC.html')

def UserInfo(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'User_info.html')