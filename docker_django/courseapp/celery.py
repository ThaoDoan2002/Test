# your_project/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Thiết lập biến môi trường cho Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courseapp.settings')

app = Celery('courseapp')

# Tải cấu hình từ settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tìm và tự động tải các task từ tất cả các ứng dụng
app.autodiscover_tasks()


# Thêm cấu hình mới
app.conf.broker_connection_retry_on_startup = True


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

