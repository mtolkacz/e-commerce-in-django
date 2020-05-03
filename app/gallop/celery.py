import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gallop.settings')


app = Celery('gallop',)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task(bind=True, ignore_result=False)
def add(self, x, y):
    print("Test add {}".format(x+y))
    return x + y


