from django.views import generic
from django.shortcuts import render, get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from .serializers import PostSerializer
from .models import Post
from comments.forms import CommentForm


def post_detail(request, slug):
    template_name = 'blog/post_detail.html'
    post = get_object_or_404(Post, slug=slug)
    comments = post.comments.filter(active=True)
    comment_form = CommentForm()

    return render(request, template_name, {'post': post,
                                           'comments': comments,
                                           'comment_form': comment_form})


class Posts(ListAPIView):
    queryset = Post.objects.filter(status=1).order_by('-created_on')
    serializer_class = PostSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'blog/posts.html'
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        latest_post = self.queryset.first()
        latest_post_serializer = self.get_serializer(latest_post)
        page = self.paginate_queryset(self.queryset.exclude(id=latest_post.id))
        data = {'latest': latest_post_serializer.data, }
        if page is not None:
            all_posts_serializer = self.get_serializer(page, many=True)
            data['posts'] = all_posts_serializer.data
            return self.get_paginated_response(data)

        serializer = self.get_serializer(self.queryset.exclude(id=latest_post.id), many=True)
        data['posts'] = serializer.data
        return Response(data)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

