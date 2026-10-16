from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("boxes/", views.box_list, name="box_list"),
    path("orders/new/", views.order_create, name="order_create"),
    path("orders/<int:order_id>/recommendation/", views.recommendation, name="recommendation"),
]
