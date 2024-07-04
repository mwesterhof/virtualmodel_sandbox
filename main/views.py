from django.views.generic import DetailView, ListView

from .models import Thing


class TestView(ListView):
    template_name = 'main/test_view.html'
    model = Thing


class TestDetailView(DetailView):
    template_name = 'main/test_detail_view.html'
    model = Thing
