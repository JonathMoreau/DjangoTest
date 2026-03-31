from django.shortcuts import render, redirect, get_object_or_404
from .models import Task

def task_list(request):
    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            Task.objects.create(title=title)

    tasks = Task.objects.all().order_by("-created_at")
    return render(request, "todo/task_list.html", {"tasks": tasks})

def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.is_done = not task.is_done
    task.save()
    return redirect("task_list")