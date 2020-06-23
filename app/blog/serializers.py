from rest_framework import serializers

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    created_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    author = serializers.CharField(source='author.username')

    class Meta:
        model = Post
        fields = ['id', 'slug', 'title', 'author', 'created_on', 'content', ]
