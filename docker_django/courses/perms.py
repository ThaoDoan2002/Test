from rest_framework import permissions

from .models import Payment


class IsPaymentGranted(permissions.BasePermission):
    """
    Cho phép truy cập nếu người dùng đã thanh toán cho khóa học tương ứng.
    """

    def has_object_permission(self, request, view, obj):
        """
        Kiểm tra quyền truy cập đến video.
        """
        # Lấy khóa học từ video (giả sử video có trường khóa ngoại đến Course)
        course = obj.course  # Giả sử mỗi video có liên kết với lesson, và lesson có liên kết với course

        # Kiểm tra xem người dùng đã thanh toán cho khóa học này chưa
        return Payment.objects.filter(user=request.user, course=course, status=True).exists()