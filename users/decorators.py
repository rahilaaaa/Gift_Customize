from django.shortcuts import redirect
def user_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_auth'):
            return redirect('login_user')  # Redirect to user login if not authenticated as user
        return view_func(request, *args, **kwargs)
    return wrapper