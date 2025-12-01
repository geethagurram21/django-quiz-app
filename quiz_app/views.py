import random
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.http import HttpResponseForbidden
from .forms import RegistrationForm, QuizSelectForm
from .models import Module, Question, QuizAttempt, QuestionResponse
from django.contrib.auth import get_user_model
from django.db import models as djmodels
User = get_user_model()
from django.http import JsonResponse

def api_test(request):
    return JsonResponse({"status": "ok"})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            u = form.save(commit=False)
            u.set_password(form.cleaned_data['password'])
            u.save()
            login(request, u)
            return redirect('quiz_app:choose_quiz')
    else:
        form = RegistrationForm()
    return render(request, 'quiz_app/register.html', {'form': form})
class CustomLoginView(LoginView):
    template_name = 'quiz_app/login.html'
class CustomLogoutView(LogoutView):
    next_page = 'quiz_app:login'
@login_required
def choose_quiz(request):
    modules = Module.objects.all()
    if request.method == 'POST':
        form = QuizSelectForm(request.POST)
        if form.is_valid():
            selected_modules = list(form.cleaned_data['modules'])
            request.session['selected_module_ids'] = [m.id for m in selected_modules]
            return redirect('quiz_app:start_quiz')
    else:
        form = QuizSelectForm()
    return render(request, 'quiz_app/choose_quiz.html', {'form': form, 'modules': modules})
@login_required
def start_quiz(request):
    module_ids = request.session.get('selected_module_ids')
    if not module_ids:
        return redirect('quiz_app:choose_quiz')
    modules = list(Module.objects.filter(id__in=module_ids))
    if not modules:
        return redirect('quiz_app:choose_quiz')
    TOTAL = 30
    num_modules = len(modules)
    per_module = TOTAL // num_modules
    remainder = TOTAL - (per_module * num_modules)
    counts = [per_module] * num_modules
    for i in range(remainder):
        counts[i % num_modules] += 1
    selected_questions = []
    for m, cnt in zip(modules, counts):
        qs = list(m.questions.all())
        if len(qs) < cnt:
            chosen = qs[:]
        else:
            chosen = random.sample(qs, cnt)
        selected_questions.extend(chosen)
    if len(selected_questions) < TOTAL:
        pool = list(Question.objects.exclude(id__in=[q.id for q in selected_questions]))
        need = TOTAL - len(selected_questions)
        if len(pool) >= need:
            selected_questions.extend(random.sample(pool, need))
        else:
            selected_questions.extend(pool)
    random.shuffle(selected_questions)
    attempt = QuizAttempt.objects.create(user=request.user, total_questions=len(selected_questions))
    attempt.modules.set(modules)
    for q in selected_questions:
        QuestionResponse.objects.create(attempt=attempt, question=q)
    request.session['current_attempt_id'] = attempt.id
    request.session['quiz_start_time'] = timezone.now().isoformat()
    request.session['quiz_length_seconds'] = 30 * 60
    return redirect('quiz_app:quiz_page', attempt_id=attempt.id)
@login_required
def quiz_page(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    responses = attempt.responses.select_related('question').all()
    qlist = []
    for r in responses:
        q = r.question
        qlist.append({
            'response_id': r.id,
            'question_id': q.id,
            'text': q.text,
            'options': q.options,
            'chosen_index': r.chosen_index
        })
    start_iso = request.session.get('quiz_start_time')
    length_seconds = request.session.get('quiz_length_seconds', 30*60)
    if start_iso:
        start_dt = datetime.fromisoformat(start_iso)
        elapsed = (timezone.now() - start_dt).total_seconds()
        remaining = max(0, int(length_seconds - elapsed))
    else:
        remaining = length_seconds
    return render(request, 'quiz_app/quiz_page.html', {
        'attempt': attempt,
        'qlist': qlist,
        'remaining_seconds': remaining
    })
@login_required
def submit_quiz(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    if request.method != 'POST':
        return HttpResponseForbidden('Only POST allowed')
    responses = attempt.responses.select_related('question').all()
    correct_count = 0
    for r in responses:
        key = f'response_{r.id}'
        val = request.POST.get(key)
        if val is None or val == '':
            r.chosen_index = None
            r.is_correct = False
        else:
            try:
                idx = int(val)
            except:
                idx = None
            r.chosen_index = idx
            if idx is not None and idx == r.question.correct_index:
                r.is_correct = True
                correct_count += 1
            else:
                r.is_correct = False
        r.save()
    attempt.score = correct_count
    attempt.completed_at = timezone.now()
    attempt.duration_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
    attempt.save()
    request.session.pop('current_attempt_id', None)
    request.session.pop('quiz_start_time', None)
    request.session.pop('quiz_length_seconds', None)
    return redirect('quiz_app:quiz_result', attempt_id=attempt.id)
@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    responses = attempt.responses.select_related('question').all()
    display = []
    for r in responses:
        q = r.question
        display.append({
            'text': q.text,
            'options': q.options,
            'correct_index': q.correct_index,
            'chosen_index': r.chosen_index,
            'is_correct': r.is_correct,
            'module': q.module.name
        })
    return render(request, 'quiz_app/quiz_result.html', {
        'attempt': attempt,
        'display': display
    })
@login_required
def history_view(request):
    attempts = request.user.quiz_attempts.order_by('-started_at')
    return render(request, 'quiz_app/history.html', {'attempts': attempts})
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_attempts = QuizAttempt.objects.count()
    avg_score = QuizAttempt.objects.exclude(score__isnull=True).aggregate(djmodels.Avg('score'))['score__avg']
    latest_attempts = QuizAttempt.objects.select_related('user').order_by('-started_at')[:20]
    return render(request, 'quiz_app/admin_dashboard.html', {
        'total_users': total_users,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'latest_attempts': latest_attempts
    })
