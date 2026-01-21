from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

def index(request):
    return render(request, 'user/index.html', {'title': 'Главная'})

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get("email")

            htmly = get_template('user/Email.html')
            d = {"username": username}
            subject, from_email, to = "welcome", 'topvovanplay23@gmail.com', email
            html_content = htmly.render(d)
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, f'Ваш аккаунт создан! Сейчас вы можете авторизоваться.')
            return redirect("login")
    else: 
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form, 'title': "Регистрация"})

def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        if user is not None:
            form = login(request,user)
            messages.success(request, f'Добро пожаловать {username}!')
            return redirect('index')
        else:
            messages.info(request, f'Аккаунт не найден!')
    form = AuthenticationForm()
    return render(request,'user/login.html', {'form': form, 'title': 'Авторизация'})
