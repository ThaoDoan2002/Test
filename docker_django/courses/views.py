import os

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from django.shortcuts import render

from rest_framework import viewsets, generics, status, parsers, permissions
from courses import serializers, paginators
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from . import perms
from .models import Category, Course, Lesson, User, Video, Payment
from .serializers import VideoSerializer


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer


class CourseViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Course.objects.filter(active=True)
    serializer_class = serializers.CourseSerializer
    pagination_class = paginators.CoursePaginator

    def get_permissions(self):
        if self.action.__eq__('courses_bought'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['get'], detail=False)
    def courses_bought(self, request):
        user = request.user
        # Lấy danh sách các khóa học mà user đã thanh toán thành công
        paid_courses_ids = Payment.objects.filter(user=user, status=True).values_list('course', flat=True)
        bought_courses = Course.objects.filter(id__in=paid_courses_ids)

        # Sử dụng paginator để phân trang
        paginator = self.paginator
        page = paginator.paginate_queryset(bought_courses, request)

        # Kiểm tra nếu có phân trang
        if page is not None:
            serializer = serializers.CourseSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        # Nếu không có phân trang, trả về tất cả dữ liệu
        serializer = serializers.CourseSerializer(bought_courses, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def lessons(self, request, pk):
        lessons = self.get_object().lesson_set.filter(active=True)
        return Response(serializers.LessonSerializer(lessons, many=True, context={'request': request}).data,
                        status=status.HTTP_200_OK)


class LessonViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = Lesson.objects.filter(active=True)
    serializer_class = serializers.LessonSerializer

    def get_permissions(self):
        if self.action.__eq__('videos'):
            return [permissions.IsAuthenticated(), perms.IsPaymentGranted()]
        return [permissions.AllowAny()]

    @action(methods=['get'], detail=True)
    def videos(self, request, pk):
        videos = self.get_object().video_set.filter(active=True)
        return Response(serializers.VideoSerializer(videos, many=True).data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.action.__eq__('current_user'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['get'], url_name='current-users', detail=False)
    def current_user(self, request):
        return Response(serializers.UserSerializer(request.user).data)


    def create(self, request, *args, **kwargs):
        # Tạo người dùng
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        user_email = serializer.data['email']
        first_name = serializer.data.get('first_name', '')
        last_name = serializer.data.get('last_name', '')

        # res = subscribe_user_to_mailchimp.delay(user_email, first_name, last_name)
        # print(res)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VideoViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = [MultiPartParser]  # Để xử lý form-data với file

    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            video_instance = serializer.save(url=None)  # Lưu instance video với url=None ban đầu

            # Kiểm tra xem 'url' có trong request.FILES hay không
            if 'url' in request.FILES:
                video_file = request.FILES['url']

                # Tạo thư mục tạm nếu chưa tồn tại
                temp_dir = '/path/to/temp/dir'  # Đường dẫn tới thư mục tạm
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)

                # Lưu tệp video tạm thời
                if isinstance(video_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
                    temp_file_path = os.path.join(temp_dir, video_file.name)
                    with open(temp_file_path, 'wb') as temp_file:
                        for chunk in video_file.chunks():
                            temp_file.write(chunk)

                    # Gửi task lên Celery để upload file lên S3
                    # upload_video_to_s3.delay(temp_file_path, video_file.name, video_instance.id)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def successed(request):
    return render(request, 'payment_successful.html')


def cancelled(request):
    return render(request, 'cancelled.html')
