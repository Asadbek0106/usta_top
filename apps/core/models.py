from django.db import models


class TimeStampedModel(models.Model):
    yaratilgan = models.DateTimeField(auto_now_add=True, db_index=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

