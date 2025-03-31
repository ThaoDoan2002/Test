import os
import uuid

from django.conf import settings
from django.contrib import admin
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.db.models import F, Sum, ExpressionWrapper
from django.template.response import TemplateResponse
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .forms import RevenueFilterForm
from .models import Category, Course, Lesson, User, Video, Payment
from .tasks import upload_video_to_s3
from django.urls import path


class CoursesAdminSite(admin.AdminSite):
    site_header = "starLight"

    def get_urls(self):
        return [
            path('course-stats/', self.stats_view, name="course-stats")
        ] + super().get_urls()

    def stats_view(self, request):
        form = RevenueFilterForm(request.GET or None)
        payments = Payment.objects.filter(status=True)

        if form.is_valid():
            course = form.cleaned_data.get('course')
            time_filter = form.cleaned_data.get('time_filter')

            if course:
                payments = payments.filter(course=course)

            # Lọc theo thời gian
            if time_filter == 'month':
                payments = payments.annotate(period=F('created_date__month'))
            elif time_filter == 'year':
                payments = payments.annotate(period=F('created_date__year'))

            # Tính tổng doanh thu theo period
            revenue_data = payments.values('period').annotate(
                total_revenue=Sum('course__price')
            ).order_by('period')

            print(list(revenue_data))  # Kiểm tra cấu trúc của revenue_data

            # Lấy dữ liệu period và revenue
            periods = [data['period'] for data in revenue_data]
            revenues = [data['total_revenue'] for data in revenue_data]
        else:
            periods = []
            revenues = []

        context = {
            'form': form,
            'periods': periods,
            'revenues': revenues,
        }
        return TemplateResponse(request, 'admin/stats.html', context)


admin_site = CoursesAdminSite(name='myapp')


class LessonInlineAdmin(admin.StackedInline):
    model = Lesson
    extra = 1
    fk_name = 'course'



class CourseAdmin(ImportExportModelAdmin):
    inlines = [LessonInlineAdmin ]




class UserAdmin(admin.ModelAdmin):
    list_display = ['pk', 'username']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name']
    search_fields = ['name']
    list_filter = ['id', 'name']


class VideoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Đặt giá trị url = None
        obj.url = None
        super().save_model(request, obj, form, change)

        # Kiểm tra và xử lý upload video
        if 'url' in request.FILES:
            video_file = request.FILES['url']
            temp_dir = '/path/to/temp/dir'  # Thay đổi đường dẫn tới thư mục tạm

            # Tạo thư mục tạm nếu chưa tồn tại
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Lưu file tạm thời và gọi task Celery
            if isinstance(video_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
                temp_file_path = os.path.join(temp_dir, video_file.name)
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in video_file.chunks():
                        temp_file.write(chunk)
                # Gửi task lên Celery để upload file lên S3
                upload_video_to_s3.delay(temp_file_path, video_file.name, obj.id)


admin_site.register(Video, VideoAdmin)
admin_site.register(Category)
admin_site.register(Course)
admin_site.register(Lesson)
admin_site.register(User)

