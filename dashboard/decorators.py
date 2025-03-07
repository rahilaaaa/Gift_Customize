from django.shortcuts import redirect
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_auth'):
            return redirect('login_admin')  # Redirect to admin login if not authenticated as admin
        return view_func(request, *args, **kwargs)
    return wrapper
