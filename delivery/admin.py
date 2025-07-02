from django.contrib import admin
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule

admin.site.register(PeriodicTask)
admin.site.register(IntervalSchedule)
admin.site.register(CrontabSchedule)
admin.site.register(SolarSchedule)
admin.site.register(ClockedSchedule)
