from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import Choice, Question, Vote


def superuser_required(view_func):
    return login_required(user_passes_test(lambda user: user.is_superuser)(view_func))


class IndexView(generic.ListView):
    template_name = "app/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        return (
            Question.objects.filter(pub_date__lte=timezone.now())
            .prefetch_related("choices")
            .order_by("-pub_date")[:6]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["poll_cards"] = [{"question": question} for question in context["latest_question_list"]]
        return context


class DetailView(generic.DetailView):
    model = Question
    template_name = "app/detail.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now()).prefetch_related("choices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submitted_name"] = ""
        context["selected_choice_id"] = None
        return context


class ResultsView(generic.DetailView):
    model = Question
    template_name = "app/results.html"

    def get_queryset(self):
        return Question.objects.prefetch_related("choices")


def vote(request, question_id):
    question = get_object_or_404(Question.objects.prefetch_related("choices"), pk=question_id)
    if question.pub_date > timezone.now():
        messages.error(request, "This poll is not open yet.")
        return redirect("app:index")
    if request.method != "POST":
        return redirect("app:detail", pk=question.pk)

    voter_name = request.POST.get("voter_name", "").strip()
    choice_id = request.POST.get("choice")
    selected_choice = question.choices.filter(pk=choice_id).first() if choice_id else None

    errors = []
    if not voter_name:
        errors.append("Please enter your name.")
    if selected_choice is None:
        errors.append("Please choose an option.")

    if errors:
        return render(
            request,
            "app/detail.html",
            {
                "question": question,
                "errors": errors,
                "submitted_name": voter_name,
                "selected_choice_id": int(choice_id) if choice_id and choice_id.isdigit() else None,
            },
            status=400,
        )

    with transaction.atomic():
        Choice.objects.filter(pk=selected_choice.pk).update(votes=F("votes") + 1)
        Vote.objects.create(question=question, choice=selected_choice, voter_name=voter_name)

    messages.success(request, "Your vote has been recorded.")
    return HttpResponseRedirect(reverse("app:results", args=(question.id,)))


@superuser_required
def dashboard(request):
    selected_question = None
    selected_poll_id = request.GET.get("poll")
    search_query = request.GET.get("q", "").strip()
    questions_queryset = Question.objects.prefetch_related(
        Prefetch("choices", queryset=Choice.objects.order_by("id"))
    )
    if search_query:
        questions_queryset = questions_queryset.filter(question_text__icontains=search_query)

    paginator = Paginator(questions_queryset, 5)
    page_obj = paginator.get_page(request.GET.get("page"))
    questions = page_obj.object_list

    if selected_poll_id:
        selected_question = get_object_or_404(questions_queryset, pk=selected_poll_id)
    elif questions:
        selected_question = questions[0]

    context = {
        "questions": questions,
        "page_obj": page_obj,
        "search_query": search_query,
        "selected_question": selected_question,
        "recent_votes": Vote.objects.select_related("question", "choice")[:8],
        "published_count": questions_queryset.filter(pub_date__lte=timezone.now()).count(),
        "total_votes": sum(question.total_votes for question in questions_queryset),
        "create_poll_data": {"question_text": "", "pub_date": ""},
    }
    return render(request, "app/dashboard.html", context)


@superuser_required
def question_create(request):
    if request.method != "POST":
        return redirect("app:dashboard")
    question_text = request.POST.get("question_text", "").strip()
    pub_date_raw = request.POST.get("pub_date", "").strip()
    try:
        parsed_pub_date = timezone.datetime.strptime(pub_date_raw, "%Y-%m-%dT%H:%M")
        pub_date = timezone.make_aware(parsed_pub_date, timezone.get_current_timezone())
    except ValueError:
        pub_date = None

    if question_text and pub_date is not None:
        question = Question.objects.create(question_text=question_text, pub_date=pub_date)
        messages.success(request, "Poll created.")
        return redirect(f"{reverse('app:dashboard')}?poll={question.pk}")
    messages.error(request, "Please correct the poll form.")
    return render(
        request,
        "app/dashboard.html",
        {
            "questions": Question.objects.prefetch_related("choices"),
            "selected_question": None,
            "recent_votes": Vote.objects.select_related("question", "choice")[:8],
            "published_count": Question.objects.filter(pub_date__lte=timezone.now()).count(),
            "total_votes": Vote.objects.count(),
            "create_poll_data": {"question_text": question_text, "pub_date": pub_date_raw},
            "form_errors": ["Question and publish date are required in the correct format."],
        },
        status=400,
    )


@superuser_required
def question_update(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method != "POST":
        return redirect(f"{reverse('app:dashboard')}?poll={pk}")
    question_text = request.POST.get("question_text", "").strip()
    pub_date_raw = request.POST.get("pub_date", "").strip()
    try:
        parsed_pub_date = timezone.datetime.strptime(pub_date_raw, "%Y-%m-%dT%H:%M")
        pub_date = timezone.make_aware(parsed_pub_date, timezone.get_current_timezone())
    except ValueError:
        pub_date = None

    if question_text and pub_date is not None:
        question.question_text = question_text
        question.pub_date = pub_date
        question.save(update_fields=["question_text", "pub_date"])
        messages.success(request, "Poll updated.")
    else:
        messages.error(request, "Poll update failed.")
    return redirect(f"{reverse('app:dashboard')}?poll={pk}")


@superuser_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == "POST":
        question.delete()
        messages.success(request, "Poll deleted.")
    return redirect("app:dashboard")


@superuser_required
def choice_create(request, question_pk):
    question = get_object_or_404(Question, pk=question_pk)
    if request.method != "POST":
        return redirect(f"{reverse('app:dashboard')}?poll={question_pk}")
    choice_text = request.POST.get("choice_text", "").strip()
    if choice_text:
        Choice.objects.create(question=question, choice_text=choice_text)
        messages.success(request, "Choice added.")
    else:
        messages.error(request, "Choice could not be added.")
    return redirect(f"{reverse('app:dashboard')}?poll={question_pk}")


@superuser_required
def choice_update(request, pk):
    choice = get_object_or_404(Choice.objects.select_related("question"), pk=pk)
    if request.method == "POST":
        choice_text = request.POST.get("choice_text", "").strip()
        if choice_text:
            choice.choice_text = choice_text
            choice.save(update_fields=["choice_text"])
            messages.success(request, "Choice updated.")
        else:
            messages.error(request, "Choice update failed.")
    return redirect(f"{reverse('app:dashboard')}?poll={choice.question.pk}")


@superuser_required
def choice_delete(request, pk):
    choice = get_object_or_404(Choice.objects.select_related("question"), pk=pk)
    question_pk = choice.question.pk
    if request.method == "POST":
        choice.delete()
        messages.success(request, "Choice deleted.")
    return redirect(f"{reverse('app:dashboard')}?poll={question_pk}")
