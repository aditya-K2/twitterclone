"""twitterserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import json
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
# from django.views.decorators.csrf import csrf_exempt
from . import database
import datetime
import jwt

SECRET_JWT = "GROUP_7"
def home(request):
    if 'JWT_KEY' in request.COOKIES:
        try:
            data = jwt.decode(request.COOKIES["JWT_KEY"], SECRET_JWT, algorithms=["HS256"])
        except:
            return redirect('/vlogin')
        context = { "user_id" : data["user_id"],
                    "posts" : database.get_home_time_line(data["user_id"]),
                    "upper_bar_title" : "Home"}
        return render(request, 'home.html', context)
    else:
        return redirect('/vlogin')

def user(request, user_id):
    if 'JWT_KEY' in request.COOKIES:
        try:
            data = jwt.decode(request.COOKIES["JWT_KEY"], SECRET_JWT, algorithms=["HS256"])
        except:
            return redirect('/vlogin')
        context = { "user_id" : data["user_id"],
                    "posts" : database.get_user_time_line(user_id),
                    "upper_bar_title" : user_id}
        if not database.user_exists(user_id) : return render(request, "error.html")
        if data["user_id"] != user_id:
            context["notself"] = "True"
            context["nuser"] = user_id
            context["followstatus"] = database.get_follow_relation(data["user_id"], user_id)
        return render(request, 'home.html', context)
    else:
        return redirect('/vlogin')

def create_tweet(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    database.insert_tweet(body_data["user_id"], body_data["tweet_body"])
    return HttpResponse()

def tweet(request, tweet_id):
    if 'JWT_KEY' in request.COOKIES:
        try:
            data = jwt.decode(request.COOKIES["JWT_KEY"], SECRET_JWT, algorithms=["HS256"])
        except:
            return redirect('/vlogin')
        result = database.get_tweet_time_line(tweet_id)
        context = { "user_id" : data["user_id"],
                    "comments" : ( result["comments"] if "comments" in result else []),
                    "tweet" : result["tweet"],
                    "upper_bar_title" : 'Tweet'}
        return render(request, 'tweet.html', context)
    else:
        return redirect('/vlogin')

def retweet_render(request, subtweet_id):
    if 'JWT_KEY' in request.COOKIES:
        try:
            data = jwt.decode(request.COOKIES["JWT_KEY"], SECRET_JWT, algorithms=["HS256"])
        except:
            return redirect('/vlogin')
        context = { "user_id" : data["user_id"],
                    "subtweet_id" : subtweet_id,
                    "upper_bar_title" : 'Retweet'}
        return render(request, 'retweet.html', context)
    else:
        return redirect('/vlogin')

def retweet(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    database.insert_retweet(body_data["user_id"], body_data["retweet_body"], body_data["subtweet_id"])
    return HttpResponse()

def comment_on_tweet(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    database.insert_comment(body_data["user_id"], body_data["comment_body"], body_data["parent_tweet"])
    return HttpResponse()

def login(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    response = HttpResponse()
    if database.check_user(body_data["user_id"], body_data["password"]):
        jwt_key = jwt.encode({ "user_id" : body_data["user_id"], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, SECRET_JWT, )
        response.set_cookie("JWT_KEY", jwt_key)
        response.status_code = 200
    else:
        response.status_code = 400
    return response

def signin(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    response = HttpResponse()
    if database.signin(body_data["user_id"], body_data["password"]):
        jwt_key = jwt.encode({ "user_id" : body_data["user_id"], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, SECRET_JWT, )
        response.set_cookie("JWT_KEY", jwt_key)
        response.status_code = 200
    else:
        response.status_code = 400
    return response

def follow(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    database.follow(body_data["user_id"], body_data["follows"])
    return HttpResponse()

def delete(request, tweet_id):
    database.delete_tweet(tweet_id)
    if 'JWT_KEY' in request.COOKIES:
        try:
            data = jwt.decode(request.COOKIES["JWT_KEY"], SECRET_JWT, algorithms=["HS256"])
        except:
            return redirect('/vlogin')
        context = { "user_id" : data["user_id"],
                    "posts" : database.get_home_time_line(data["user_id"]),
                    "upper_bar_title" : "Home"}
        return render(request, 'home.html', context)
    else:
        return redirect('/vlogin')

def vlogin(request):
    return render(request, 'login.html')

def slash(request):
    if 'JWT_KEY' in request.COOKIES:
        try:
            jwt.decode(request.COOKIES["JWT_KEY"], SECRET_JWT, algorithms=["HS256"])
        except:
            return redirect('/vlogin')
        return redirect('/home')
    else:
        return redirect('/vlogin')


urlpatterns = [
    path('', slash),
    path('admin/', admin.site.urls),
    path('home/', home),
    path('user/<str:user_id>', user, name="user_timeline"),
    path('create_tweet/', create_tweet),
    path('tweet/<str:tweet_id>', tweet, name="tweet_timeline"),
    path('comment_on_tweet/', comment_on_tweet),
    path('login/', login),
    path('vlogin/', vlogin),
    path('signin/', signin),
    path('retweet/<str:subtweet_id>', retweet_render, name="retweet_render"),
    path('retweet/', retweet, name="retweet"),
    path('follow/', follow),
    path('delete/<str:tweet_id>', delete)
]+ static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
