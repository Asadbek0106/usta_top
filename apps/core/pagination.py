from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Sahifalash: ?page=2&page_size=50 (sukut bo'yicha 20 ta, ko'pi bilan 100 ta)."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
