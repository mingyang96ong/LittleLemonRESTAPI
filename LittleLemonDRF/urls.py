from django.urls import path, include

from .views import (MenuItemView, SingleMenuItemView, CategoryView, SingleCategoryView, ManagerGroupView
, RemoveManagerGroupView, DeliveryCrewGroupView, RemoveDeliveryCrewGroupView
, CartView, OrderListView, SingleOrderView, UserView)
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from djoser.views import TokenCreateView, TokenDestroyView

CustomRouter = DefaultRouter()
CustomRouter.register('users', UserView, basename='')

urlpatterns = [
    path('', include(CustomRouter.urls)),
    path('users/login', TokenCreateView.as_view(), name='login'),
    path('users/logout', TokenDestroyView.as_view(), name='logout'),
    path('category', CategoryView.as_view()),
    path('category/<int:pk>', SingleCategoryView.as_view()),
    path('menu-items', MenuItemView.as_view(), name='menu-items'),
    path('menu-items/<int:pk>', SingleMenuItemView.as_view()),
    path('groups/manager/users', ManagerGroupView.as_view()),
    path('groups/manager/users/<int:userId>', RemoveManagerGroupView.as_view()),
    path('groups/delivery-crew/users', DeliveryCrewGroupView.as_view()),
    path('groups/delivery-crew/users/<int:userId>', RemoveDeliveryCrewGroupView.as_view()),
    path('cart/menu-items', CartView.as_view()),
    path('orders', OrderListView.as_view()),
    path('orders/<int:pk>', SingleOrderView.as_view())
]