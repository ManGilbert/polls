import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from faker import Faker

from app.models import Choice, Question, Vote


class Command(BaseCommand):
    help = "Seed the database with sample poll questions, choices, and votes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of poll questions to create. Maximum is 20.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing poll data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        requested_count = options["count"]
        if requested_count < 1:
            raise CommandError("Count must be at least 1.")

        count = min(requested_count, 20)
        if requested_count > 20:
            self.stdout.write(
                self.style.WARNING("Requested count exceeded 20. Seeding 20 records instead.")
            )

        if options["clear"]:
            Vote.objects.all().delete()
            Choice.objects.all().delete()
            Question.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing poll data cleared."))

        fake = Faker()
        Faker.seed()

        question_topics = [
            "Which learning format helps you most",
            "What should the next student event focus on",
            "Which campus service needs priority improvement",
            "What is your preferred exam preparation method",
            "Which communication channel should the school use more",
            "What time is best for student workshops",
            "Which library feature matters most to you",
            "What type of training should be added next semester",
        ]
        choice_banks = [
            ["Live class", "Recorded lesson", "Group discussion", "Practice quiz"],
            ["Career talk", "Innovation fair", "Sports day", "Community outreach"],
            ["Wi-Fi speed", "Library hours", "Help desk", "Transport updates"],
            ["Past papers", "Study groups", "Short notes", "Revision labs"],
            ["Email", "SMS alerts", "Portal notice", "WhatsApp updates"],
            ["Early morning", "Midday", "Late afternoon", "Weekend"],
            ["More seats", "Longer hours", "Digital access", "Quiet zones"],
            ["Coding lab", "Research writing", "Public speaking", "Entrepreneurship"],
        ]

        created_questions = 0
        now = timezone.now()

        for _ in range(count):
            topic = random.choice(question_topics)
            descriptor = fake.word().replace("_", " ").title()
            question = Question.objects.create(
                question_text=f"{topic}: {descriptor}?",
                pub_date=now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
            )

            choices = []
            for choice_text in random.sample(random.choice(choice_banks), k=4):
                choices.append(Choice.objects.create(question=question, choice_text=choice_text))

            vote_total = random.randint(3, 14)
            for _vote in range(vote_total):
                selected_choice = random.choice(choices)
                Vote.objects.create(
                    question=question,
                    choice=selected_choice,
                    voter_name=fake.name(),
                )
                Choice.objects.filter(pk=selected_choice.pk).update(votes=F("votes") + 1)

            created_questions += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created_questions} poll records with sample choices and votes.")
        )
