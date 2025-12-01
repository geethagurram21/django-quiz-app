from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
class Module(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    def __str__(self):
        return self.name
class Question(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    options = models.JSONField()
    correct_index = models.IntegerField()
    def correct_answer(self):
        try:
            return self.options[self.correct_index]
        except Exception:
            return None
    def __str__(self):
        return f"{self.module.name}: {self.text[:60]}"
class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    modules = models.ManyToManyField(Module)
    total_questions = models.IntegerField(default=30)
    score = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return f"Quiz #{self.id} by {self.user} on {self.started_at.date()}"
class QuestionResponse(models.Model):

    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    chosen_index = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    class Meta:
        unique_together = ('attempt', 'question')
    def chosen_answer(self):
        if self.chosen_index is None: return None
        try:
            return self.question.options[self.chosen_index]
        except:
            return None
 