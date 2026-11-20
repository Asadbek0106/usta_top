from django.db import connection
from django.http import JsonResponse


def health(request):
    """Server va baza tirikligini tekshiradi.

    Docker (healthcheck), load balancer yoki monitoring shu manzilga so'rov yuboradi.
    Bu oddiy Django view: DRF'ning autentifikatsiya va throttling'idan o'tmaydi.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})
