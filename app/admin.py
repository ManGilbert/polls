from django.contrib import admin

from .models import Choice, Question, Vote


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Schedule", {"fields": ["pub_date"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "is_active", "pub_date", "was_published_recently"]
    list_filter = ["is_active", "pub_date"]
    search_fields = ["question_text"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["voter_name", "question", "choice", "created_at"]
    list_filter = ["created_at", "question"]
    search_fields = ["voter_name", "question__question_text", "choice__choice_text"]


admin.site.register(Choice)
