from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Your name",
        widget=forms.TextInput(attrs={
            "class": "block w-full rounded-xl border border-slate-700 bg-slate-900/80 py-2 px-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
            "placeholder": "John Doe",
        }),
    )
    email = forms.EmailField(
        label="Your email",
        widget=forms.EmailInput(attrs={
            "class": "block w-full rounded-xl border border-slate-700 bg-slate-900/80 py-2 px-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
            "placeholder": "you@example.com",
        }),
    )
    subject = forms.CharField(
        max_length=150,
        label="Subject",
        widget=forms.TextInput(attrs={
            "class": "block w-full rounded-xl border border-slate-700 bg-slate-900/80 py-2 px-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
            "placeholder": "Question about AI Travel Planner",
        }),
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={
            "class": "block w-full rounded-xl border border-slate-700 bg-slate-900/80 py-2 px-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500",
            "rows": 5,
            "placeholder": "Write your question or feedback here…",
        }),
    )