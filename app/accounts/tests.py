from time import sleep

from django.test import SimpleTestCase

from . import tasks


class MailTestCase(SimpleTestCase):
    def test_send_email_celery(self):
        task = tasks.send_email.apply_async(('michal.tolkacz@gmail.com', 'test', 'test'), )
        while not task.ready():
            sleep(0.5)
        result_output = task.get()
        self.assertEqual(result_output, True)


class CeleryTestCase(SimpleTestCase):
    def test_example_delay_task(self):
        task = tasks.add.delay(5, 6)
        while not task.ready():
            sleep(0.5)
        result_output = task.get()
        print(result_output)
        self.assertEqual(result_output, 11)

    def test_access_to_database(self):
        task = tasks.get_first_product.delay()
        while not task.ready():
            sleep(0.5)
        result_output = task.get()
        print(result_output)
        #self.assertEqual(len(result_output), 1)
