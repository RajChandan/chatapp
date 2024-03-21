import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Room,Message

class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        print(self.room_name,' === room name')
        print(self.scope,' === scope')
        self.room_group_name = f'chat_{self.room_name}'
        self.room = Room.objects.get(name=self.room_name)
        self.user = self.scope['user']

        self.accept()
        print(self.channel_layer,' ==== channel layer')
        print(self.channel_name,' === channnel name')
        async_to_sync(self.channel_layer.group_add)(self.room_group_name,self.channel_name)

        self.send(json.dumps({
        'type': 'user_list',
        'users': [user.username for user in self.room.online.all()],
    }))
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_send)(self.room_group_name,{'type':'user_join','user':self.user.username})
        
        self.room.online.add(self.user)
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name,self.channel_name)
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_send)(self.room_group_name,{'type':'user_leave','user':self.user.username})
        
        self.room.online.remove(self.user)

    
    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if not self.user.is_authenticated:
            return

        async_to_sync(self.channel_layer.group_send)(self.room_group_name,{'type':'chat_message','message':message,'user':self.user.username})

        Message.objects.create(user=self.user,room=self.room,content=message)
    
    def chat_message(self,event):
        self.send(text_data=json.dumps(event))

    def user_join(self,event):
        self.send(text_data=json.dumps(event))
    
    def user_leave(self,event):
        self.send(text_data=json.dumps(event))