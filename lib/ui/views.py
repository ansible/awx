from django.views.generic.base import TemplateView

class IndexView(TemplateView):

    template_name = 'ui/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        # Add any additional context info here.
        return context

index = IndexView.as_view()
