from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from .forms import ContactForm

# Create your views here.
def faq_view(request):
    faqs = [
        {
            "question": "What is the AI Travel Planner?",
            "answer": (
                "The AI Travel Planner is a web-based application built with Django, "
                "LangChain, and travel APIs that generates personalized, day-wise travel "
                "itineraries based on your destination, budget, duration, and preferences."
            ),
            "tag": "General"
        },
        {
            "question": "How does the itinerary generation work?",
            "answer": (
                "Once you provide your trip details, the system validates your inputs, "
                "fetches real-time data from travel and weather APIs, and uses an LLM via "
                "LangChain to build an optimized day-wise itinerary with activities, food "
                "suggestions, and cost estimates."
            ),
            "tag": "How it works"
        },
        {
            "question": "What inputs do I need to provide?",
            "answer": (
                "You need to provide your destination, trip dates or duration, and budget range. "
                "Optionally, you can specify preferences like adventure vs relaxation, cultural "
                "focus, food interests, and preferred travel pace."
            ),
            "tag": "Usage"
        },
        {
            "question": "What kind of output does the AI generate?",
            "answer": (
                "The system generates a structured day-wise plan including sightseeing, local "
                "experiences, food recommendations, estimated daily costs, and weather-aware "
                "suggestions."
            ),
            "tag": "Output"
        },
        {
            "question": "Does the system use real-time data?",
            "answer": (
                "Yes. It integrates weather and travel APIs for forecasts, approximate attraction "
                "costs, local transport and meal estimates, and seasonal advisories."
            ),
            "tag": "Real-time data"
        },
        {
            "question": "Can I modify or regenerate itineraries?",
            "answer": (
                "Yes. You can change your budget, duration, or preferences and regenerate a new "
                "plan. You can also tweak individual days or request alternate suggestions for "
                "specific activities or meals."
            ),
            "tag": "Customization"
        },
        {
            "question": "Which technologies are used in this project?",
            "answer": (
                "The stack includes Django for backend, LangChain for AI orchestration, an LLM "
                "provider (such as OpenAI), travel and weather APIs for data, Tailwind CSS and "
                "JavaScript for the frontend, and Django ORM with SQLite or PostgreSQL for data "
                "persistence."
            ),
            "tag": "Tech stack"
        },
        {
            "question": "Does the platform make bookings?",
            "answer": (
                "No. The AI Travel Planner focuses on planning and recommendations. It does not "
                "perform direct bookings or handle payments. You can use the itinerary as a guide "
                "for booking on external platforms."
            ),
            "tag": "Limitations"
        },
        {
            "question": "Is the project production-ready?",
            "answer": (
                "The architecture is designed to be scalable, with modular LangChain pipelines, "
                "Django-based backend, and support for caching and containerization. With proper "
                "infrastructure and API key management, it can be extended to production use."
            ),
            "tag": "Scalability"
        },
        {
            "question": "Who is this project for?",
            "answer": (
                "It is ideal for travelers who want personalized itineraries, for startups exploring "
                "AI-based travel products, and for showcasing end-to-end skills in Django, "
                "LangChain, and travel API integrations."
            ),
            "tag": "Audience"
        },
    ]

    context = {
        "faqs": faqs,
        "page_title": "FAQ: AI Travel Planner",
    } 
    return render(request, "core/faq.html", context)


def terms_view(request):
    context = {
        "page_title": "Terms of Service – AI Travel Planner",
        "company_name": "AI Travel Planner",
        "last_updated": "10 December 2025",
        "support_email": "amanpyproject@gmail.com",
    }
    return render(request, "core/terms.html", context)


def privacy_view(request):
    context = {
        "page_title": "Privacy Policy – AI Travel Planner",
        "company_name": "AI Travel Planner",
        "last_updated": "10 December 2025",
        "support_email": "amanpyproject@gmail.com",
    }
    return render(request, "core/privacy.html", context)


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            full_subject = f"[AI Travel Planner] {subject}"
            body = (
                f"New contact message from AI Travel Planner:\n\n"
                f"Name: {name}\n"
                f"Email: {email}\n\n"
                f"Message:\n{message}"
            )

            support_email = getattr(settings, "CONTACT_SUPPORT_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)

            recipient_list = [support_email] if support_email else []

            if not recipient_list:
                messages.error(
                    request,
                    "Email backend is not configured. Please set CONTACT_SUPPORT_EMAIL or DEFAULT_FROM_EMAIL in settings."
                )
            else:
                send_mail(
                    subject=full_subject,
                    message=body,
                    from_email=support_email,
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
                messages.success(
                    request,
                    "Your message has been sent successfully. We will get back to you soon."
                )
                return redirect("core:contact")
    else:
        form = ContactForm()

    context = {
        "page_title": "Contact Us – AI Travel Planner",
        "form": form,
    }
    return render(request, "core/contact.html", context)