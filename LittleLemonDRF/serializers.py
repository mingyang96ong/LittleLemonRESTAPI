from rest_framework import serializers
from rest_framework.reverse import reverse

from django.contrib.auth.models import User, Group

from .models import MenuItem, Category, Cart, Order, OrderItem

from decimal import Decimal
import os

class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name',
     )
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            field: {'write_only': True}
            for field in ('password', 'last_login', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
        }

class CategorySerializer(serializers.ModelSerializer):
    menu_items_url = serializers.SerializerMethodField('get_related_url')
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title', 'menu_items_url']

    def get_related_url(self, category: Category):
        full_url = self.context.get('request').build_absolute_uri(reverse('menu-items'))

        return full_url + '?search={}'.format(category.title)

class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset = Category.objects.all()
        , slug_field = 'title'
    )
    
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']
        extra_kwargs = {'price': {'min_value': Decimal("0.00")}}

class CartSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        # many=True,
        read_only=True,
        slug_field='username',
     )
    menuitem = MenuItemSerializer(read_only=True)
    
    # This will give a BrowsableAPI a better view with restricted set of dropdown values
    menuitem_id = serializers.PrimaryKeyRelatedField(
        queryset = MenuItem.objects.all()
        , write_only = True
    )

    class Meta:
        model = Cart
        fields = ['user','menuitem', 'menuitem_id', 'quantity', 'price', 'unit_price']
        extra_kwargs = {
            'price': {'read_only': True}
            , 'unit_price': {'read_only': True}
        }
    
    def save(self, **kwargs):
        menuitem = self.validated_data['menuitem_id']
        if not menuitem:
            raise serializers.ValidationError({
                'menuitem_id': "This menuitem_id '{}' is not valid".format(self.validated_data['menuitem_id'])
            })
        
        quantity = self.validated_data['quantity']
        unit_price = menuitem.price
        price = quantity * unit_price
        user = kwargs['user']

        new_cart = Cart.objects.create(user=user, menuitem=menuitem, quantity=quantity, price=price, unit_price=unit_price)
        return new_cart

class DynamicWriteOnlySerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        if type(super) == type(self):
            writeable_fields = kwargs.get('writeable_fields', [])
        else:
            writeable_fields = kwargs.pop('writeable_fields', [])
        
        super().__init__(*args, **kwargs)
        writeable_fields_set = set(writeable_fields) if type(writeable_fields) == list else {writeable_fields}

        if hasattr(self, 'read_only') and self.read_only == True and writeable_fields_set:
            read_only_fields = set(self.fields)
            self.read_only = False
        else:
            read_only_fields = set(k for k, v in self.fields.items() if v.read_only)
        
        fields = {k: v for k, v in self.fields.items()}
        for field in self.fields:
            if field in writeable_fields_set:
                self.fields[field].read_only = False
                read_only_fields.remove(field)
            elif self.fields[field].write_only:
                fields.pop(field)
            if self.fields[field].read_only:
                read_only_fields.add(field)
        self.Meta.read_only_fields = tuple(read_only_fields)
        self.fields = fields
    
class OrderSerializer(DynamicWriteOnlySerializer):
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    
    delivery_crew_id = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.filter(groups__name='Delivery Crew').all()
        , write_only=True
        , source = 'delivery_crew__id'
    )
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'delivery_crew_id']

class OrderItemSerializer(DynamicWriteOnlySerializer): # Since this is only use in BrowsableAPIView GET, we can make every field `read_only` = True
    order = OrderSerializer(read_only=True)
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        read_only_fields = ('order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price')
        extra_kwargs = {'price': {'min_value': Decimal("0.00")}}

class ManagerOrderItemSerializer(DynamicWriteOnlySerializer): # Since this is only use in BrowsableAPIView GET, we can make every field `read_only` = True
    order = OrderSerializer(read_only=True, writeable_fields = ['delivery_crew_id'])
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        read_only_fields = ('order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price')
        extra_kwargs = {'price': {'min_value': Decimal("0.00")}}

class DeliveryCrewOrderItemSerializer(DynamicWriteOnlySerializer): # Since this is only use in BrowsableAPIView GET, we can make every field `read_only` = True
    order = OrderSerializer(read_only=True, writeable_fields = ['status'])
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        read_only_fields = ('order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price')
        extra_kwargs = {'price': {'min_value': Decimal("0.00")}}