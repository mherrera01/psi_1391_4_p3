from django.shortcuts import render, redirect
from django.urls import reverse


def home(request):
    context_dict = {}
    context_dict["usuario"] = "Pepe"
    return render(request, 'core/home.html', context_dict)


def login(request):
    return redirect(reverse('home'))
