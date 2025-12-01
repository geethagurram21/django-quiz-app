from django.contrib import admin
from .models import Module, Question, QuizAttempt, QuestionResponse
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'module', 'correct_index')
    list_filter = ('module',)
    search_fields = ('text',)
class QuestionResponseInline(admin.TabularInline):
    model = QuestionResponse
    readonly_fields = ('question', 'chosen_index', 'is_correct')
    extra = 0
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'started_at', 'completed_at', 'score')
    list_filter = ('started_at', 'modules',)
    inlines = [QuestionResponseInline]
