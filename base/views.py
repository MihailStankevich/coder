
from email import message
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.contrib.auth import authenticate, login, logout

from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
# Create your views here.
def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST': #if the form is sent 
        email = request.POST.get('email').lower() #from the sent form we take the username and password
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email) #checking if the user exists
        except:
            messages.error(request, 'User does not exist')#unless print flash message

        user = authenticate(request, email=email, password=password)#если пользователь существует, проверяем пароль и юзернэйм. Возвращает User если совпали данные и пользователь нашелся и  None если нет ползователя с таким именем и паролем

        if user is not None: #if everythin good , user will be logged in and redirected to the home page
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exit' )
    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    page = 'register'
    form = MyUserCreationForm()
    if request.method == 'POST' :
        form = MyUserCreationForm(request.POST) #getting data from the form (password and username)
        if form.is_valid() :
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registretion' )
    return render(request, 'base/login_register.html',{'page': page, 'form':form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else '' #if in q there is smth we filter rooms by q .  WE get this q from searching bar (name) or by topic's name  (topic_component line 11 and navbar line 16)
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    ) #we search for rooms that contains q in their topic's name

    topics = Topic.objects.all()[0:5]
    room_counter = rooms.count()

    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    
    context = {'rooms': rooms, 'topics': topics, 'room_counter': room_counter, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all() #gives us a set of messages related to this room. We get all children of room class
    participants = room.participants.all()
    if request.method == 'POST': #if the form was sent
        message = Message.objects.create( # we create a object with Message class
        user=request.user,
        room=room,
        body=request.POST.get( 'body')
        )
        room.participants.add(request.user)
        return redirect( 'room' , pk=room.id)
    
    context = {'room': room, 'room_messages': room_messages, 'participants':participants}
    return render(request, 'base/room.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all() # getting all children (room) from a parent User
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_messages':room_messages, 'topics':topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm() # our form from .forms.py
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name' ),
            description=request.POST.get(' description'),
        )
        return redirect('home')
        # form = RoomForm(request.POST) #data from out submited form
        # if form.is_valid():
        #     room = form.save(commit=False) #if everything's valid , dats will be saved in db
        #     room.host = request.user
        #     room.save() 
        

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk): #pass pk cause we need to update a certain room
    room = Room.objects.get(id=pk) #get room by its pk
    form = RoomForm(instance=room) #already has data prefilled in the form  
    topics = Topic.objects.all() 
    if request.user != room.host: #if the current user is not the room host
        return HttpResponse( 'You are not allowed here' )

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.topic=topic
        room.name=request.POST.get('name')
        room.description=request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form' : form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html' , context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host: #if the current user is not the room host
        return HttpResponse( 'You are not allowed here' )

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user: #if the current user is not the room host
        return HttpResponse( 'You are not allowed here' )

    if request.method == 'POST':
        message.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect ('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {"topics": topics})

def activityPage(request):
    room_messages = Message.objects.all()[:3]
    return render(request, 'base/activity.html', {'room_messages': room_messages})