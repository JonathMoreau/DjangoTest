from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Task


@login_required
def task_list(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        if title:
            Task.objects.create(title=title, owner=request.user)
            return redirect("task_list")

    tasks = Task.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "todo/task_list.html", {"tasks": tasks})


@login_required
@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.is_done = not task.is_done
    task.save(update_fields=["is_done"])
    return redirect("task_list")
