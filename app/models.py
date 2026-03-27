from django.db import models
from django.urls import reverse
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=255)
    pub_date = models.DateTimeField("date published")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-pub_date", "-id"]

    def __str__(self):
        return self.question_text

    def get_absolute_url(self):
        return reverse("app:detail", args=[self.pk])

    def was_published_recently(self):
        now = timezone.now()
        return now - timezone.timedelta(days=1) <= self.pub_date <= now

    def is_published(self):
        return self.pub_date <= timezone.now()

    @property
    def total_votes(self):
        return sum(choice.votes for choice in self.choices.all())


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    choice_text = models.CharField(max_length=255)
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.choice_text


class Vote(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="votes_log",
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="vote_entries",
    )
    voter_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.voter_name} -> {self.choice.choice_text}"
