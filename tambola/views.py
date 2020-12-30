from django.shortcuts import render

from datetime import datetime

from django import forms
from tambola.forms import *
from tambola.models import *
from django.shortcuts import render, redirect
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from django.utils import timezone

from django.http import HttpResponse, Http404
import json
from django.views.decorators.csrf import ensure_csrf_cookie
import numpy as np

from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
import random


# Create your views here.
@ensure_csrf_cookie
@login_required
def action_home(req):
    if(req.method == "GET"):
        return render(req, 'tambola/home.html',{"form" : roomForm()})
    #post method, joining a room
    if(req.method == "POST" and req.POST["roomName"]):
        return redirect(reverse("room",kwargs={"room_name":req.POST["roomName"]}))


# Function to generate random ticket
def generate_ticket_json(request, room_name):
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=403)
    
    # check if gameroom is associated with user and has same room_name, get old_ticket
    if GameRoom.objects.filter(profile = request.user.user_profile.first()):
        game_room = GameRoom.objects.filter(profile = request.user.user_profile.first())[0]
        if game_room.room_stats.room_name == room_name:
            old_ticket = game_room.ticket
            old_clicked = game_room.clicked
            return old_ticket, old_clicked


    ticket = np.full(27,1).reshape(9,3)
    ticket[:4,:] *= 0
    [np.random.shuffle(ticket[:,i]) for i in range(3)]

    for i in range(9):
        num = np.arange(1,10)
        np.random.shuffle(num)
        num = np.sort(num[:3])
        ticket[i,:] *= (num + i * 10)

    # transform ticket
    ticket = ticket.T
    
    row_top = []
    for n in ticket[0]:
        row_top.append(str(n))
    row_middle = []
    for n in ticket[1]:
        row_middle.append(str(n))
    row_bottom = []
    for n in ticket[2]:
        row_bottom.append(str(n))  

    print(ticket)          
    
    response_data = {'row_top' : row_top, 'row_middle' : row_middle, 'row_bottom' : row_bottom}
    response_json = json.dumps(response_data)    
    new_ticket = Ticket(ticket_json = response_json)
    new_ticket.save()

    clicked_data = dict()
    for i,v in enumerate(row_top):
        if v!="0":
            clicked_data[i] = False
        else:
            clicked_data[str(i)] = True
    for i,v in enumerate(row_middle):
        if v!="0":
            clicked_data[str(i + 10)] = False
        else:
            clicked_data[str(i + 10)] = True
    for i,v in enumerate(row_bottom):
        if v!="0":
            clicked_data[str(i + 20)] = False
        else:
            clicked_data[str(i + 20)] = True

    new_clicked = ClickList(clickList_json = json.dumps(clicked_data))
    new_clicked.save()

    
    
    numbers_pot = json.dumps(list())
    numbers_called = json.dumps(list())
    winners = json.dumps({})
    chat = json.dumps({})
    room_stats = None
    try:
        room_stats = GameRoomStats.objects.filter(room_name= room_name)[0]
        print("GameRoomStats for already exists for ", room_name)
    except:    
        room_stats = GameRoomStats(room_name=room_name, numbers_pot=numbers_pot, numbers_called=numbers_called, winners = winners, chat = chat, host = request.user.username)
        room_stats.save()
        print("GameRoomStats created for ", room_name)

    game_room = GameRoom(profile=request.user.user_profile.first(), room_stats = room_stats, ticket = new_ticket, clicked = new_clicked)
    game_room.save()
   
  
    return new_ticket, new_clicked

def _my_json_error_response(message, status=200):
    # You can create your JSON by constructing the string representation yourself (or just use json.dumps)
    response_json = '{ "error": "' + message + '" }'
    return HttpResponse(response_json, content_type='application/json', status=status)
    

def users_in_room(room_name):
    game_room_obj = GameRoom.objects.filter(room_stats_id=room_name)
    game_room_obj_val = game_room_obj.values()
    users_in_room = []
    
    for i in game_room_obj_val:
        curr_id = i['profile_id']
        person = User.objects.filter(id=curr_id)[0]
        users_in_room.append(person.username)

    return users_in_room   

@ensure_csrf_cookie
@login_required
def room(request, room_name):
  

    new_ticket, new_clicked = generate_ticket_json(request, room_name)
    host = GameRoomStats.objects.filter(room_name= room_name)[0].host
    users = users_in_room(room_name)

    clicked_dict = json.loads(new_clicked.clickList_json)
    print("Initialize room :")
    print(clicked_dict)

    ticket_numbers = json.loads(new_ticket.ticket_json)
    print(ticket_numbers)

    displayHostButton = not host == request.user.username

    context = {'room_name': room_name,'user_profile': request.user.user_profile.first(), 'ticket_numbers':ticket_numbers, "host":host, "ishost": displayHostButton, "users_in_room":users }
    return render(request, 'tambola/room.html', context)


def room_serializer(request,room_name):

    ticket_numbers, ticket_clicked = generate_ticket_json(request,room_name)

    ticket_numbers = json.loads(ticket_numbers.ticket_json)
    ticket_clicked = json.loads(ticket_clicked.clickList_json)

    list_of_marked_values = []
    for i,v in enumerate(ticket_numbers["row_top"]):
        if ticket_clicked[str(i)] == True and v != '0':
                list_of_marked_values.append(v)
    for i,v in enumerate(ticket_numbers["row_middle"]):
        if ticket_clicked[str(i+10)] == True and v != '0':
                list_of_marked_values.append(v) 
    for i,v in enumerate(ticket_numbers["row_bottom"]):
        if ticket_clicked[str(i+20)] == True and v != '0':
                list_of_marked_values.append(v)
    print(list_of_marked_values)
    response_json = json.dumps(list_of_marked_values)
    response = HttpResponse(response_json, content_type = "application/json")
    return response

def click_button(request):
    button_num = request.POST["button_num"]
    room_name = request.POST["room_name"]

    ticket_numbers, ticket_clicked = generate_ticket_json(request, room_name)
    
    game_room = GameRoom.objects.filter(profile=request.user.user_profile.first())[0]

    ticket_numbers = json.loads(ticket_numbers.ticket_json)
    ticket_clicked = json.loads(ticket_clicked.clickList_json)

    print("Which number is being pressed?")
    print(button_num)

   
    numbers_called = json.loads(game_room.room_stats.numbers_called)

    if button_num in numbers_called:

        clicked_idx = find_index(button_num, ticket_numbers)
        print("ticket idx found", clicked_idx)

        ticket_clicked[clicked_idx] = True

        game_room.clicked.clickList_json = json.dumps(ticket_clicked)
        game_room.clicked.save()

        # if there are winners, it directly adds that (first) username to gamestats winner
        check_for_winner(request, ticket_clicked, ticket_numbers, game_room)

    return room_serializer(request,room_name)

def find_index(button_num, ticket_numbers):
    for i,v in enumerate(ticket_numbers["row_top"]):
        if v == button_num:
            return str(i)     
    for i,v in enumerate(ticket_numbers["row_middle"]):
         if v == button_num:
            return str(i+10)   
    for i,v in enumerate(ticket_numbers["row_bottom"]):
         if v == button_num:
            return str(i+20)   

def check_for_winner(request, ticket_clicked, ticket_numbers, game_room):
    top_count = 0
    middle_count = 0
    bottom_count = 0
    for i,v in enumerate(ticket_numbers["row_top"]):
        if ticket_clicked[str(i)] == True:
                top_count += 1
    for i,v in enumerate(ticket_numbers["row_middle"]):
        if ticket_clicked[str(i+10)] == True:
                middle_count += 1
    for i,v in enumerate(ticket_numbers["row_bottom"]):
        if ticket_clicked[str(i+20)] == True:
                bottom_count += 1
    
    winner = json.loads(game_room.room_stats.winners)
    # print("winners till now: ", winner)
    # print(top_count)
    # print(middle_count)
    # print(bottom_count)
    if top_count == 9:
        if 'Top row winner'in winner:
            print("top row winner already exists")
        else:
            winner.update({'Top row winner' : request.user.username})
            game_room.room_stats.winners = json.dumps(winner)
            game_room.room_stats.save()
    if middle_count == 9:
        if 'Middle row winner'in winner:
            print("middle row winner already exists")
        else:
            winner.update({'Middle row winner' : request.user.username})      
            game_room.room_stats.winners = json.dumps(winner)
            game_room.room_stats.save()          
    if bottom_count == 9:
        if 'Bottom row winner'in winner:
            print("bottom row winner already exists")
        else:
            winner.update({'Bottom row winner' : request.user.username}) 
            game_room.room_stats.winners = json.dumps(winner)
            game_room.room_stats.save()   
    if top_count == 9 and middle_count == 9 and bottom_count == 9:
        if 'Full House winner'in winner:
            print("full house winner already exists")
        else:
            winner.update({'Full House winner' : request.user.username}) 
            game_room.room_stats.winners = json.dumps(winner)
            game_room.room_stats.save()

    # print("winners after now: ", winner)
    

# starting game and drawing numbers

def start_game(request, room_name):
    game_room = GameRoom.objects.filter(profile=request.user.user_profile.first())[0]
    currnumpot = json.loads(game_room.room_stats.numbers_pot)

    if len(currnumpot) == 0:
        pot_numbers = map(str,  list(range(1, 91)))
        numbers_pot = json.dumps(list(pot_numbers))
        game_room.room_stats.numbers_pot = numbers_pot
        game_room.room_stats.save()
    
    numbers_called = json.loads(game_room.room_stats.numbers_called)
    numbers_pot = json.loads(game_room.room_stats.numbers_pot)

    return HttpResponse("Game room stats initialized")

@database_sync_to_async
def _get_gameroom_numbers(request):
    game_room = GameRoom.objects.filter(profile=request.user.user_profile.first())[0]
    numbers_called = game_room.room_stats.numbers_called
    numbers_pot = game_room.room_stats.numbers_pot
    winners = game_room.room_stats.winners
    
    return json.loads(numbers_called), json.loads(numbers_pot), json.loads(winners)

@database_sync_to_async
def _put_gameroom_numbers(request, numbers_called, numbers_pot):
    game_room = GameRoom.objects.filter(profile=request.user.user_profile.first())[0]
    game_room.room_stats.numbers_called = json.dumps(numbers_called)
    game_room.room_stats.numbers_pot = json.dumps(numbers_pot)
    game_room.room_stats.save()


async def event_triger_number_drawn(request, room_name):
    
    numbers_called, numbers_pot, winners_dic = await _get_gameroom_numbers(request)


    # print("numbers_pot on drawing are: ", numbers_pot)
    # print("numbers_called on drawing are: ", numbers_called)

    num = numbers_pot.pop(random.randrange(len(numbers_pot)))
    numbers_called.append(num)

    await _put_gameroom_numbers(request, numbers_called, numbers_pot)
    

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        'room_%s' % room_name,
        {
            'type': 'number_drawn',
            'number': num,
            'numbers_called' : numbers_called,
            'numbers_pot' : numbers_pot,
            'winners' : json.dumps(winners_dic)
        }
    )

    return HttpResponse("Drawn!!!")
     












# req.post is the dictionary
def action_login(req):
    print("login action")
    if req.method == "GET":
        print("login_get")
        context = {"form": LoginForm()}
        return render(req, 'tambola/login.html', context)

    # post action
    form = LoginForm(req.POST)
    if not form.is_valid():
        context = {"form": form, "login_error": "Username/Password Incorrect"}
        print("login form not valid")
        return render(req, 'tambola/login.html', context)

    new_user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data['password'])

    login(req, new_user)
    return redirect(reverse("action_home"))


def action_register(req):
    print("action_reg")

    if req.method == "GET":
        context = {"form": RegisterForm()}
        return render(req, 'tambola/register.html', context)

    form = RegisterForm(req.POST)
    if not form.is_valid():
        context = {"form": form}
        print("rendering register, not valid")
        return render(req, 'tambola/register.html', context)

    # if the form is valid
    new_user = User.objects.create_user(username=form.cleaned_data['username'],
                                        password=form.cleaned_data['password'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])
    new_user.save()
    print("user registered")

    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])

    login(req, new_user)

    new_profile = Profile()
    new_profile.id_user = new_user
    new_profile.total_wins = 0
    new_profile.total_score = 0
    new_profile.save()


    return redirect(reverse('action_home'))

@login_required
def action_personal_prof(req):
    curr_prof = Profile.objects.filter(id_user = req.user)[0]
    p_form = ProfileForm(instance = curr_prof)
    context = {"profform": p_form}
    context['profile'] = curr_prof
    if req.method=="GET":
        return render(req, 'tambola/personal_profile.html',context)
    #post

    # get the arguments in the form
    p_form = ProfileForm(req.POST,req.FILES,instance = curr_prof)
    #edit example

    context = {"profform": p_form}
    context['profile'] = curr_prof
    # update the profile object
    if not p_form.is_valid():
        return render(req, 'tambola/personal_profile.html',context)
    try:
        curr_prof.content_type = p_form.cleaned_data['profile_picture'].content_type
        print("\nform saved\n")
        p_form.save()
    except:
        print("No content type change")
        p_form.save()
    return render(req, 'tambola/personal_profile.html', context)

@login_required
def get_photo(req, username):
    corr_u = User.objects.filter(username=username )[0]
    corr_prof = Profile.objects.filter(id_user=corr_u)[0]
    ctype = corr_prof.content_type
    return HttpResponse(corr_prof.profile_picture,content_type=ctype)


def action_logout(req):
    logout(req)
    return redirect(reverse('action_login'))

