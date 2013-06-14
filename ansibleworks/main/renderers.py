import rest_framework.renderers

class BrowsableAPIRenderer(rest_framework.renderers.BrowsableAPIRenderer):
    '''
    Customizations to the default browsable API renderer.
    '''

    def get_form(self, view, method, request):
        '''Never show auto-generated form (only raw form).'''
        obj = getattr(view, 'object', None)
        if not self.show_form_for_method(view, method, request, obj):
             return
        if method in ('DELETE', 'OPTIONS'):
             return True  # Don't actually need to return a form
