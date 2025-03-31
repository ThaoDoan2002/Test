import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Course, Payment, User
from .perms import IsPaymentGranted

# Cấu hình Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY
host = settings.MY_HOST


class StripeCheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk):
        try:
            # Lấy dữ liệu sản phẩm từ request
            course = Course.objects.get(id=pk)
            amount = course.price  # giá (tính bằng cents)
            user_id = request.user.id

            # Kiểm tra xem thanh toán cho khóa học này đã tồn tại hay chưa
            payment_exists = Payment.objects.filter(user_id=user_id, course_id=pk, status=True).exists()

            if payment_exists:
                print('--------------------')
                return Response(
                    {'error': 'Bạn đã mua khóa học này rồi.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Tạo phiên thanh toán của Stripe nếu thanh toán chưa tồn tại
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'vnd',
                        'product_data': {
                            'name': course.name,
                        },
                        'unit_amount': amount*1000000,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{host}/success/',
                cancel_url=f'{host}/cancel/',
                metadata={
                    'course_id': course.id,
                    'user_id': user_id,
                }
            )

            # Trả về URL của phiên thanh toán
            return Response({'checkout_url': session.url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': str(e)}, status=400)

    # Xử lý sự kiện thanh toán thành công
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Lấy metadata
        course_id = session['metadata'].get('course_id')
        user_id = session['metadata'].get('user_id')

        # Tìm user và course từ database
        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)

        # Lưu thông tin thanh toán vào database
        Payment.objects.create(
            user=user,
            course=course,
            status=True
        )

    return JsonResponse({'status': 'success'})
