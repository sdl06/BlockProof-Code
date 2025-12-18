"""
Custom DRF router that avoids format suffix converter conflicts.

DRF's DefaultRouter can register a `drf_format_suffix` path converter when
format suffix patterns are present. In some environments (notably tests),
that converter may be registered multiple times, causing:

    ValueError: Converter 'drf_format_suffix' is already registered.

We avoid this by generating the default routes via `DefaultRouter.get_urls()`
and filtering out any format-suffix URL patterns.
"""

from rest_framework.routers import DefaultRouter

class NoFormatSuffixRouter(DefaultRouter):
    """Router that strips DRF format suffix URL patterns."""

    # Critical: prevent DRF from applying `format_suffix_patterns(urls)`,
    # which registers the `drf_format_suffix` converter and crashes when
    # multiple routers are instantiated.
    include_format_suffixes = False

    def get_urls(self):
        urls = super().get_urls()

        filtered_urls = []
        for url_pattern in urls:
            pattern_str = str(url_pattern.pattern)

            # Skip patterns that explicitly handle format suffixes.
            # Covers both regex-style and path-converter style patterns.
            if (
                ".{format}" in pattern_str
                or "(?P<format>" in pattern_str
                or "drf_format_suffix" in pattern_str
            ):
                continue

            filtered_urls.append(url_pattern)

        return filtered_urls
