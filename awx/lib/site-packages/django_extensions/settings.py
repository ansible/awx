from django.conf import settings

REPLACEMENTS = {
}
add_replacements = getattr(settings, 'EXTENSIONS_REPLACEMENTS', {})
REPLACEMENTS.update(add_replacements)

