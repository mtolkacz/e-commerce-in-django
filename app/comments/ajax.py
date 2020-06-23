from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from blog.models import Post
from comments.forms import CommentForm


@require_http_methods(['POST'])
@login_required
def add(request):
    data = {}
    user = request.user
    comment_form = CommentForm(data=request.POST)
    if not comment_form.is_valid():
        data['message'] = 'Form not valid!'
    else:
        try:
            post_id = int(request.POST.get('post_id', None))
        except(TypeError, ValueError, OverflowError):
            post_id = None
            data['message'] = 'Wrong post id'
        if post_id:
            try:
                post = Post.objects.get(id=post_id)
            except post.DoesNotExist:
                post = None
                data['message'] = 'Post doesn\'t exist'
            if post:
                # Create Comment object but don't save to database yet
                new_comment = comment_form.save(commit=False)
                # Assign the current post to the comment
                new_comment.post = post
                # Save the comment to the database
                new_comment.save()
                data['success'] = True
    return JsonResponse(data)
