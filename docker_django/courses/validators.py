from django.core.exceptions import ValidationError
from moviepy.editor import VideoFileClip
import os
from tempfile import NamedTemporaryFile

def file_size(value):
    temp_file_path = None
    video = None
    try:
        # Lưu file tạm thời để moviepy có thể xử lý
        with NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(value.read())  # Ghi dữ liệu file vào file tạm
            temp_file.flush()
            temp_file_path = temp_file.name  # Lấy đường dẫn file tạm

        # Sử dụng moviepy để mở video và kiểm tra thời lượng
        video = VideoFileClip(temp_file_path)
        duration = video.duration  # Thời lượng video tính bằng giây

        # Kiểm tra nếu video dài hơn 15 phút (900 giây)
        if duration > 15 * 60:  # 15 phút tính bằng giây
            raise ValidationError("Video phải có thời lượng dưới 15 phút.")
    except Exception as e:
        raise ValidationError(f"Lỗi khi xử lý video: {e}")
    finally:
        # Đảm bảo đóng video trước khi xóa file tạm
        if video:
            video.close()

        # Xóa file tạm sau khi xử lý xong
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except PermissionError:
                raise ValidationError("Không thể xóa file tạm thời vì nó đang được sử dụng.")

    return value
