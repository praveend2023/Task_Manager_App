import json
import os
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.conf import settings
from django.shortcuts import render

TASKS_FILE = os.path.join(settings.BASE_DIR, 'tasks.json')

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f)

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        user = User.objects.create_user(username=username, password=password)
        return JsonResponse({'message': 'User registered successfully'})
    except Exception as e:
        return JsonResponse({'error': 'Registration failed', 'details': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        token = get_token(request)
        return JsonResponse({'message': 'Login successful', 'token': token})
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})

@csrf_exempt
@require_http_methods(["GET"])
def task_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    tasks = load_tasks()
    user_tasks = tasks.get(str(request.user.id), [])
    return JsonResponse({'tasks': user_tasks})

@csrf_exempt
@require_http_methods(["POST"])
def task_add(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    data = json.loads(request.body)
    task_text = data.get('task')
    if not task_text:
        return JsonResponse({'error': 'Task text required'}, status=400)
    tasks = load_tasks()
    user_id = str(request.user.id)
    user_tasks = tasks.get(user_id, [])
    task_id = str(uuid.uuid4())
    user_tasks.append({'id': task_id, 'task': task_text})
    tasks[user_id] = user_tasks
    save_tasks(tasks)
    return JsonResponse({'message': 'Task added', 'task_id': task_id})

@csrf_exempt
@require_http_methods(["DELETE"])
def task_delete(request, task_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    tasks = load_tasks()
    user_id = str(request.user.id)
    user_tasks = tasks.get(user_id, [])
    new_tasks = [t for t in user_tasks if t['id'] != task_id]
    if len(new_tasks) == len(user_tasks):
        return JsonResponse({'error': 'Task not found'}, status=404)
    tasks[user_id] = new_tasks
    save_tasks(tasks)
    return JsonResponse({'message': 'Task deleted'})

def index(request):
    return render(request, 'testapp/index.html')
