import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tambola.models import *

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name'] #extract room_name from url
        self.room_group_name = 'room_%s' % self.room_name #place users in this group
        connection_user = self.scope["user"] #This is USER Object, get username from it

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'on_connection_message',
                'connection_user' : connection_user,
                'connection_msg' : 'New User Joined',
            }
        )


    async def on_connection_message(self, event):
        connection_msg = event['connection_msg']
        connection_user = event['connection_user']
        await self.send(text_data = json.dumps({
            'connection_user' : connection_user.username,
            'connection_msg' : connection_msg,
        }))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        
        # "group_send" is to send to Group ASGI (another function will actually "self.send")
        await self.channel_layer.group_send( 
            self.room_group_name,
            {
                'type': 'chatroom_message',
                'message': message,
                'username': username,
            }
        )

    async def chatroom_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

    async def number_drawn(self, event):
        print("EVENT TRIGERED")
        number = event['number']
        numbers_called = event['numbers_called']
        numbers_pot= event['numbers_pot']
        winners = event['winners']
        await self.send(text_data = json.dumps({
            'number_drawn' : number,
            'numbers_called' : numbers_called,
            'numbers_pot' : numbers_pot,
            'winners' : winners,
        }))

    


    # @database_sync_to_async
    # def put_gameroom_chat(self, username, message):
    #     game_room = GameRoom.objects.filter(profile=connection_user)[0]
    #     chat = json.loads(game_room.room_stats.chat)
    #     print(chat)
    #     chat.update({username : message})
    #     print("after", chat)
    #     game_room.room_stats.chat = json.dumps(chat)
    #     game_room.room_stats.save()    

    #     return chat