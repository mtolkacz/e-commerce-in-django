from __future__ import absolute_import, unicode_literals

import os
from celery import Celery
from celery.schedules import crontab
from celery import shared_task


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gallop.settings')


app = Celery('gallop',)

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    "every day at 10 AM": {
        "task": "cart_reminder",  # <---- Name of task
        "schedule": crontab(hour='12',
                            minute=0,
                            )
    },
}

app.autodiscover_tasks()


@shared_task(bind=True,
             name='xxx_execute_xx_task',
             max_retries=3,
             soft_time_limit=20)
def xxx_execute_xx_task(self):
    pass

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task(bind=True, ignore_result=False)
def add(self, x, y):
    print("Test add {}".format(x+y))
    return x + y


