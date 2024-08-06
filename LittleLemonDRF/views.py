from django.shortcuts import render, get_object_or_404

from rest_framework import generics
from rest_framework import views
from rest_framework.permissions import IsAuthenticated

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from rest_framework.response import Response

from django.contrib.auth.models import User, Group

from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import ( MenuItemSerializer, UserSerializer, CartSerializer
, OrderItemSerializer, CategorySerializer, ManagerOrderItemSerializer, DeliveryCrewOrderItemSerializer)
from .permissions import IsManagerOrAdmin, IsCustomer, IsDeliveryCrew, IsAdmin

from .paginator import StandardResultsSetPagination

from djoser import signals
from djoser.conf import settings
from djoser.compat import get_user_email
from djoser.views import UserViewSet

from decimal import Decimal

from datetime import datetime

# Create your views here. #menu-items
class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    ordering_fields = '__all__'
    search_fields = ['category__title']

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]
    
    def post(self, request):
        new_menu_item = MenuItemSerializer(data=request.POST)
        if new_menu_item.is_valid():
            new_menu_item.save()
            return Response(new_menu_item.data, status=HTTP_201_CREATED)
        return Response(new_menu_item.errors, status=HTTP_400_BAD_REQUEST)


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method in ('PUT', 'PATCH'):
            return [IsAuthenticated(), IsManagerOrAdmin()]
        return [IsAuthenticated(), IsAdmin()]
    
    def put(self, request, pk):
        data = request.data
        menu_item = get_object_or_404(MenuItem, pk=pk)
        
        serialized_item = self.serializer_class(data=data)

        if not serialized_item.is_valid():
            return Response(serialized_item.errors, status=HTTP_400_BAD_REQUEST)

        for k, v in serialized_item.validated_data.items():
            if self.request.user.is_superuser or k == 'featured': # Admin or Manager can only edit 'featured' field
                setattr(menu_item, k, v)
        menu_item.save()
        return Response(self.serializer_class(menu_item).data, status=HTTP_200_OK)

    def patch(self, request, pk):
        return self.put(request, pk)
    

class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]


class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]

class ManagerGroupView(generics.ListCreateAPIView):
    user_group_name = "Manager"
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        user_group_name = self.__class__.user_group_name
        return User.objects.filter(groups__name=user_group_name)

    def post(self, request):
        user_data = request.POST
        user_group_name = self.__class__.user_group_name
        selected_user = get_object_or_404(User, pk=user_data['userId'])
        
        if selected_user.groups.filter(name=user_group_name).exists():
            return Response('User is already a {}'.format(user_group_name), status=HTTP_400_BAD_REQUEST)
        
        manager_group = Group.objects.get(name=user_group_name)

        # manager_group.user_set.add(selected_user)
        selected_user.groups.add(manager_group)
        return Response('user added to {} group'.format(user_group_name), status=HTTP_200_OK)


class RemoveManagerGroupView(generics.DestroyAPIView):
    user_group_name = "Manager"
    serializer_class = UserSerializer

    def get_queryset(self):
        user_group_name = self.__class__.user_group_name
        return User.objects.filter(groups__name=user_group_name)

    def delete(self, request, userId):
        selected_user = get_object_or_404(User, pk=userId)
        user_group_name = self.__class__.user_group_name

        if not selected_user.groups.filter(name=user_group_name).exists():
            return Response('User is not a {}'.format(user_group_name), status=HTTP_400_BAD_REQUEST)
        
        manager_group = Group.objects.get(name=user_group_name).user_set
        manager_group.remove(selected_user)
        return Response(UserSerializer(selected_user).data, status=HTTP_200_OK)


class DeliveryCrewGroupView(ManagerGroupView):
    user_group_name = 'Delivery Crew'


class RemoveDeliveryCrewGroupView(RemoveManagerGroupView):
    user_group_name = 'Delivery Crew'


class CartView(views.APIView):
    serializer_class = CartSerializer

    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Cart.objects.filter(user__id = self.request.user.id).all()

    def get(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data, status=HTTP_200_OK)
    
    def post(self, request): # Take in distinct menu item in POST and check past record and add the quantity
        data = {k:v for k,v in request.POST.items()}

        if 'user' not in data:
            data['user'] = request.user.id
        
        check_fields = ('menuitem_id', 'quantity')

        for field in check_fields:
            if field not in data:
                return Response("'{}' is missing from request body".format(field), status=HTTP_400_BAD_REQUEST)

        menuitem_info = MenuItem.objects.filter(id=data['menuitem_id']).first()
        if not menuitem_info:
            return Response("menuitem_id '{}' does not exist".format(data['menuitem_id']))

        cart_serializer = CartSerializer(data=data)

        if cart_serializer.is_valid(): # We make good use of serializer
            # 1. We want to check if we have previous record of same user_id and menu item
            # 2. If yes, update the old record
            # 3. Else, just save the new cart item record
            user_cart_info = Cart.objects.select_related('user', 'menuitem').filter(user__id = request.user.id).filter(menuitem_id=data['menuitem_id']).first()

            if user_cart_info:
                user_cart_info.quantity += cart_serializer.validated_data.get('quantity', 0)
                user_cart_info.price += menuitem_info.price * cart_serializer.validated_data.get('quantity', 0)
                user_cart_info.save()
                return Response(CartSerializer(user_cart_info).data, status=HTTP_200_OK)
            else:
                new_cart_obj = cart_serializer.save(user=self.request.user)
                return Response(CartSerializer(new_cart_obj).data, status=HTTP_201_CREATED)
        
        return Response(new_cart_item.errors, status=HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        queryset = self.get_queryset()
        queryset.delete()
        return Response("Cart has successfully cleared", status=HTTP_200_OK)


class OrderListView(views.APIView):
    # GET List Customer -> Show all the order created by the user
    # GET List Manager -> Returns all orders with order items by all users
    # Get List Delivery Crew -> Gets all orders assigned to them
    # POST Customer -> Creates a new order item for the current user. 
    # Gets current cart items from the cart endpoints and adds those items to the order items table. Then deletes all items from the cart for this user.\

    serializer_class = OrderItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), (IsCustomer | IsManagerOrAdmin | IsDeliveryCrew)()]
        return [IsAuthenticated(), IsCustomer()]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager'):
            return OrderItem.objects.select_related('order', 'menuitem').order_by('order__id').all()
        if self.request.user.groups.filter(name='Customer'):
            order_ids = list(map(lambda x: x.id, Order.objects.filter(user__id = self.request.user.id)))
            return OrderItem.objects.select_related('order', 'menuitem').filter(order__id__in = order_ids)
        if self.request.user.groups.filter(name='Delivery Crew'):
            order_ids = list(map(lambda x: x.id, Order.objects.filter(delivery_crew__id = self.request.user.id)))
            return OrderItem.objects.select_related('order', 'menuitem').filter(order__id__in = order_ids)
        return []

    def get(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data, status=HTTP_200_OK)

    def post(self, request):
        all_carted_items = Cart.objects.filter(user__id = self.request.user.id)

        if all_carted_items.first(): #Check if there is at least one item
            total = sum(map(lambda x: x.price, all_carted_items))
            now = datetime.now()
            new_order = Order.objects.create(
                user = self.request.user
                , total = total
                , date = now
            )
            new_order.save()

            for carted_item in all_carted_items:
                new_order_item = OrderItem.objects.create(
                    order = new_order
                    , menuitem = carted_item.menuitem
                    , quantity = carted_item.quantity
                    , unit_price = carted_item.unit_price
                    , price = carted_item.price
                )
                new_order_item.save()
                carted_item.delete()
            return Response("All carted items has placed order successfully.", status=HTTP_201_CREATED)
        else:
            return Response("There is no items in your cart.", status=HTTP_400_BAD_REQUEST)


class SingleOrderView(views.APIView):
    # GET customer -> Returns all items for this order id
    # GET delivery crew -> Can view all the items in the order id if it is assigned to him
    # Get Manager -> Can view any order id

    # PUT, PATCH manager -> Updates the order's delivery crew
    # PUT, PATCH delivery crew -> Update complete status

    # DELETE manager -> Delete an order
    # serializer_class = OrderItemSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), (IsCustomer | IsManagerOrAdmin | IsDeliveryCrew)()]
        if self.request.method in ("PUT", "PATCH"):
            return [IsAuthenticated(), (IsManagerOrAdmin | IsDeliveryCrew)()]
        if self.request.method in ("DELETE"):
            return [IsAuthenticated(), IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self, unauthorized=False):
        cls = self.__class__
        if unauthorized:
            cls.serializer_class = OrderItemSerializer
        elif self.isRole('Manager') or self.request.user.is_superuser:
            cls.serializer_class = ManagerOrderItemSerializer
        elif self.isRole('Delivery Crew'):
            cls.serializer_class = DeliveryCrewOrderItemSerializer
        else:
            cls.serializer_class = OrderItemSerializer
        return cls.serializer_class

    def isValidOrderId(self, pk):
        return Order.objects.filter(id = pk).exists()

    def isRole(self, group_name):
        return self.request.user.groups.filter(name=group_name).exists()
    
    def get(self, request, pk):
        serializer_class = self.get_serializer_class(unauthorized=True)
        if not self.isValidOrderId(pk):
            return Response("Order id '{}' does not exists".format(pk), status=HTTP_400_BAD_REQUEST)
        if self.isRole('Manager') or self.request.user.is_superuser or \
        (self.isRole('Customer') and Order.objects.filter(id = pk).filter(user__id = self.request.user.id)) or \
        (self.isRole('Delivery Crew') and Order.objects.filter(id = pk).filter(delivery_crew__id = self.request.user.id)):
            serializer_class = self.get_serializer_class()
            return Response(self.__class__.serializer_class(OrderItem.objects.filter(order = pk).all(), many=True).data, status=HTTP_200_OK)

        return Response("You are not authorized to view this order id.", status=HTTP_403_FORBIDDEN)

    def put(self, request, pk):
        serializer_class = self.get_serializer_class()
        if self.isRole('Manager') or self.request.user.is_superuser:
            serialized_data = serializer_class(data=request.data)

            if not serialized_data.is_valid():
                return Response(serialized_data.errors, status=HTTP_400_BAD_REQUEST)
            
            if not self.isValidOrderId(pk):
                return Response("Order id '{}' does not exists".format(pk), status=HTTP_400_BAD_REQUEST)
            delivery_crew = serialized_data.validated_data.get('order', {}).get('delivery_crew__id', None)
            
            if not delivery_crew:
                return Response('Delivery crew id does not exists', status=HTTP_400_BAD_REQUEST)
            
            if not (delivery_crew is None or delivery_crew.groups.filter(name='Delivery Crew').exists()):
                return Response('Delivery crew id \'{}\' given is not a \'Delivery Crew\''.format(delivery_crew.id), status=HTTP_400_BAD_REQUEST)
            
            order = Order.objects.get(id=pk)
            order.delivery_crew_id = delivery_crew.id
            order.save()
            return Response("Order id \'{}\' is assigned to Delivery Crew \'{}\'".format(pk, delivery_crew.id), status=HTTP_200_OK)
        if self.isRole('Delivery Crew'):
            # Check it is valid order id
            if not self.isValidOrderId(pk):
                return Response("Order id '{}' does not exists".format(pk), status=HTTP_400_BAD_REQUEST)
            if not Order.objects.filter(pk=pk).filter(delivery_crew__id=self.request.user.id).exists():
                return Response("You are not authorised to modify this order id.", status=HTTP_403_FORBIDDEN)
            
            serialized_data = serializer_class(data=request.data)
            if not serialized_data.is_valid():
                return Response(serialized_data.errors, status=HTTP_400_BAD_REQUEST)
            
            order = Order.objects.get(id=pk)
            order.status = serialized_data.validated_data.get('order', {}).get('status', False)
            order.save()
            return Response("Order id \'{}\' status is updated to \'{}\'".format(pk, order.status), status=HTTP_200_OK)
        return Response("You are not authorized to view this api endpoint.", status=HTTP_403_FORBIDDEN)
        
    def patch(self, request, pk):
        return self.put(request, pk)


class UserView(UserViewSet):
    serializer_class = UserSerializer
    def perform_create(self, serializer, *args, **kwargs):
        user = serializer.save(*args, **kwargs)

        # Add user to 'Customer' User Group
        if Group.objects.filter(name='Customer').exists():
            customer_group = Group.objects.get(name='Customer')
            user.groups.add(customer_group)
            user.save()

        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

        context = {"user": user}
        to = [get_user_email(user)]
        if settings.SEND_ACTIVATION_EMAIL:
            settings.EMAIL.activation(self.request, context).send(to)
        elif settings.SEND_CONFIRMATION_EMAIL:
            settings.EMAIL.confirmation(self.request, context).send(to)