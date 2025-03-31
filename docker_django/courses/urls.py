import stripe
from django.urls import path, include
from rest_framework import routers
from courses import views
from .stripe_utils import StripeCheckoutViewSet,stripe_webhook

router = routers.DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='categories')
router.register('courses', views.CourseViewSet, basename='courses')
router.register('lessons', views.LessonViewSet, basename='lessons')
router.register('users', views.UserViewSet, basename='users')
router.register('videos', views.VideoViewSet, basename='videos')
router.register('payments', StripeCheckoutViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('success/', views.successed, name="success"),
    path('cancel/', views.successed, name="cancel"),
    path('webGoHooks/', stripe_webhook, name='stripe_webhook'),
]
