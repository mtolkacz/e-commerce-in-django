from django.db import models


class Entry(models.Model):
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=1000)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    pub_date = models.DateTimeField()
    comments_count = models.IntegerField()
