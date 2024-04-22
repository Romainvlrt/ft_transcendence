from django import forms
import random
from Transcendance.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import check_password
from collections import OrderedDict
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import uuid
from django.forms.widgets import FileInput
import re


class AccountCreationForm(forms.ModelForm):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'autocomplete': 'off'}))

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            self.add_error('username', "Ce nom d'utilisateur existe déjà. ❌")
        if len(username) < 4:
            self.add_error('username', "Le nom d'utilisateur doit contenir 4 caracteres minimum ❌")
        if not re.match(r'^[a-zA-Z0-9.@+-]+$' , username):
            self.add_error('username', 'Le nom d\'utilisateur ne doit contenir que des lettres, des chiffres et @/./+/- ❌')
        return username
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if len(password) < 6:
            self.add_error('password', "Le mot de passe doit contenir 6 caracteres minimum ❌")
        return password
    
    def clean_confirm_password(self):
        confirm_password = self.cleaned_data.get('confirm_password')
        password = self.cleaned_data.get('password')
        
        if confirm_password != password:
           self.add_error('confirm_password', "Les mots de passe ne sont pas identique. Veuillez les saisir a nouveau ❌")
        return confirm_password
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', "Cet email existe déjà. ❌")
        return email

    def Create_User(self, request):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        user = User.objects.create_user(username=username, email=email, password=password)
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            user.is_online = True
            user.save()
        return user

class AccountLoginForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'autocomplete': 'off'}))
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ['email', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        return cleaned_data
    
    def Login(self, request):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            return True
        else:
            self.add_error('email', "L'email ou le mot de passe est incorrect. ❌")
            return False

class RegularAccountUpdateForm(forms.ModelForm):
    username = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'autocomplete': 'off'}), help_text="Pour modifier votre email, veuillez remplir le champs mot de passe.")
    password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)
    avatar = forms.ImageField(required=False, widget=FileInput)

    def __init__(self, *args, **kwargs):
        super(RegularAccountUpdateForm, self).__init__(*args, **kwargs)
        new_order = ['username', 'first_name', 'last_name', 'email', 'password', 'new_password', 'confirm_password', 'avatar']
        self.fields = OrderedDict((f, self.fields[f]) for f in new_order)
        self.user = User.objects.get(username=self.initial.get('username'))


    class Meta:
        model = User
        fields = [
            'username', 
            'first_name',
            'last_name',
            'email',
            'password',
            'avatar',
            ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username_initial = self.initial.get('username')

        if User.objects.filter(username=username).exists() and username != username_initial:
            self.add_error('username', "Ce nom d'utilisateur existe déjà. ❌")

        if username == "" or username == None:
            self.add_error('username', "Le nom d'utilisateur ne peut pas être vide. ❌")
        
        if len(username) < 4:
            self.add_error('username', "Le nom d'utilisateur doit contenir 4 caracteres minimum ❌")

        if not re.match(r'^[a-zA-Z0-9.@+-]+$' , username):
            self.add_error('username', 'Le nom d\'utilisateur ne doit contenir que des lettres, des chiffres et @/./+/- ❌')

        return username
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        return last_name
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email == "":
            return email

        if email:
            try:
                validate_email(email)
            except ValidationError:
                self.add_error('email', "Ceci n'est pas une adresse email valide. ❌")

            if User.objects.filter(email=email).exists():
                self.add_error('email', "Cet email existe déjà. ❌")

        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        return password 
    
    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password == "":
            return new_password
        if len(new_password) < 6:
            self.add_error('new_password', "Le mot de passe doit contenir 6 caracteres minimum ❌")
        return new_password
    
    def clean_confirm_password(self):
        confirm_password = self.cleaned_data.get('confirm_password')
        new_password = self.cleaned_data.get('new_password')
        if new_password == "":
            return ""
        if confirm_password != new_password:
            self.add_error('confirm_password', "Les mots de passe ne sont pas identique. Veuillez les saisir a nouveau ❌")

        return confirm_password

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if avatar != self.user.avatar:
            try:
                from PIL import Image
                Image.open(avatar)
            except Exception:
                self.add_error('avatar', "Le fichier uploadé n'est pas une image valide. ❌")
        return avatar

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        avatar = cleaned_data.get('avatar')
        
        if username == self.user.username and first_name == self.user.first_name and last_name == self.user.last_name and email == "" and new_password == "" and confirm_password == "" and avatar == self.user.avatar:
            self.add_error('username', "Aucun champ n'a été modifié. ❌")

        if avatar != self.user.avatar:
            if "default_avatar" not in str(self.user.avatar):
                self.user.avatar.delete()
            unique_id = uuid.uuid4()
            avatar.name = f"{unique_id}.jpg"

        if email and not password:
            self.add_error('password', "Pour modifier votre email, veuillez remplir le champs mot de passe. ❌")
        if email and password and check_password(password, self.user.password) == False:
            self.add_error('password', "Le mot de passe est incorrect. ❌")

        
        if new_password and not password:
            self.add_error('password', "Pour modifier votre mot de passe, veuillez remplir le champs mot de passe. ❌")
        if new_password and password and confirm_password and check_password(password, self.user.password) == False:
            self.add_error('password', "Le mot de passe est incorrect. ❌")
        if new_password and password and not confirm_password:
            self.add_error('confirm_password', "Veuillez confirmer votre mot de passe. ❌")
        elif new_password and password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Les mots de passe ne sont pas identique. Veuillez les saisir a nouveau ❌")

        return cleaned_data

    def save(self, commit=True):
        # Exclude the password from the saved fields
        user = super(RegularAccountUpdateForm, self).save(commit=False)
        username = self.cleaned_data.get('username')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('new_password')
        new_password = self.cleaned_data.get('new_password')
        avatar = self.cleaned_data.get('avatar')

        update_field = []
        if username:
            update_field.append('username')
        if first_name:
            update_field.append('first_name')
        if last_name:
            update_field.append('last_name')
        if email:
            update_field.append('email')
        if new_password:
            user.set_password(new_password)
            update_field.append('password')
        if avatar != self.user.avatar:
            user.avatar = avatar
            update_field.append('avatar')
        if commit:
            user.save(update_fields=update_field)
        return user
    
class Auth42AccountUpdateForm(forms.ModelForm):
    username = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'autocomplete': 'off'}))
    avatar = forms.ImageField(required=False, widget=FileInput)

    def __init__(self, *args, **kwargs):
        super(Auth42AccountUpdateForm, self).__init__(*args, **kwargs)
        self.user = User.objects.get(username=self.initial.get('username'))

    class Meta:
        model = User
        fields = [
            'username', 
            'first_name',
            'last_name',
            'email',
            'avatar',
            ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username_initial = self.initial.get('username')

        if User.objects.filter(username=username).exists() and username != username_initial:
            self.add_error('username', "Ce nom d'utilisateur existe déjà. ❌")

        if username == "" or username == None:
            self.add_error('username', "Le nom d'utilisateur ne peut pas être vide. ❌")
        
        if len(username) < 4:
            self.add_error('username', "Le nom d'utilisateur doit contenir 4 caracteres minimum ❌")

        if not re.match(r'^[a-zA-Z0-9.@+-]+$' , username):
            self.add_error('username', 'Le nom d\'utilisateur ne doit contenir que des lettres, des chiffres et @/./+/- ❌')

        return username
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        return last_name
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                validate_email(email)
            except ValidationError:
                self.add_error('email', "Ceci n'est pas une adresse email valide. ❌")
        return email
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        print(f"✅avatar: {str(avatar)}")
        if avatar != self.user.avatar:
            try:
                from PIL import Image
                Image.open(avatar)
            except Exception:
                self.add_error('avatar', "Le fichier uploadé n'est pas une image valide. ❌")
    
            self.user.avatar.delete()
            unique_id = uuid.uuid4()
            avatar.name = f"{unique_id}.jpg"
            print(f"🔥avatar: {str(avatar)}")
        return avatar
    
    