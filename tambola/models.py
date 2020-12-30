from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    profile_picture = models.FileField(upload_to="./pics", default="tambola/defaultpic.png")
    bio_input_text = models.CharField(max_length = 500, default = "Default no bio yet")
    # user foreign key
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_profile")
    # followed_users = models.ManyToManyField(User, symmetrical=False, related_name='followed_users')
    content_type = models.CharField(max_length = 500, default = "image/jpeg")

    total_score = models.IntegerField()
    total_wins = models.IntegerField()

class Ticket(models.Model):
    ticket_json = models.JSONField()
    # row_top_marked = models.BooleanField(default=False) 
    # row_middle_marked = models.BooleanField(default=False) 
    # row_bottom_marked = models.BooleanField(default=False)

class ClickList(models.Model):
    clickList_json = models.JSONField()

class GameRoomStats(models.Model):
    room_name = models.CharField(max_length = 100, primary_key=True)
    numbers_pot = models.JSONField()
    numbers_called = models.JSONField()
    winners = models.JSONField()
    chat = models.JSONField()
    host = models.CharField(max_length = 100)

class GameRoom(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="profile_gameroom", primary_key=True)
    room_stats = models.ForeignKey(GameRoomStats, on_delete=models.CASCADE, related_name="roomstats_gameroom")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="ticket_gameroom")
    clicked = models.ForeignKey(ClickList, on_delete=models.CASCADE, related_name="clicked_gameroom")

