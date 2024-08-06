# from django.test import TestCase, LiveServerTestCase
from rest_framework.test import APITestCase, APIClient

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from django.contrib.auth.models import User, Group

from LittleLemonDRF.models import Category, MenuItem, Order, OrderItem
from LittleLemonDRF.serializers import MenuItemSerializer, OrderItemSerializer, OrderSerializer

import urllib
import json
from requests.auth import _basic_auth_str

# Create your tests here.
class MenuItemTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.all_groups = ['Manager', 'Delivery Crew', 'Customer']
        self.admin = 'Admin'

        self.endpoints = {
            'login': '/api/users/login'
            , 'register': '/api/users/'
            , 'menu-items': '/api/menu-items'
            , 'category': '/api/category'
            , 'manager-group': '/api/groups/manager/users'
            , 'orders': '/api/orders'
            , 'cart': '/api/cart/menu-items'
        }

        self.setup_persistent_user_accounts_and_groups()
        self.setup_persistent_categories()
        self.setup_persistent_menu_items()
        self.setup_persistent_orders()

    def setup_persistent_user_accounts_and_groups(self):
        # Create Admin and all users
        admin = self.admin
        admin_account = User(username=admin)
        admin_account.set_password(admin)
        admin_account.is_superuser = True
        admin_account.save()

        for group_name in self.all_groups:
            group = Group(name=group_name)
            group.save()
            user_account = User(username=group_name)
            user_account.set_password(group_name)
            user_account.save()

            user_account.groups.add(group)
            user_account.save()

            admin_account.groups.add(group)
        
        admin_account.save()

    def setup_persistent_categories(self):
        category_data = [
            {'title': 'Main'}
            , {'title': 'Beverage'}
            , {'title': 'Appetizer'}
            , {'title': 'Dessert'}
        ]

        for data in category_data:
            Category(**data).save()

    def setup_persistent_menu_items(self):
        data = [
            {
                "title": "Apple Juice"
                , "price": 6.10
                , "featured": False
                , "category": "Beverage" 
            }
            , {
                "title": "Coca Cola"
                , "price": 4.10
                , "featured": False
                , "category": "Beverage" 
            }
            , {
                "title": "Carbonara"
                , "price": 14.90
                , "featured": True
                , "category": "Main" 
            }
            , {
                "title": "Cheesy Pull-Apart Bread"
                , "price": 11.20
                , "featured": False
                , "category": "Appetizer"
            }
            , {
                "title": "Brownies"
                , "price": 3.6
                , "featured": False
                , "category": "Dessert"
            }
        ]

        for item in data:
            item['category'] = Category.objects.get(title=item['category'])
            MenuItem(**item).save()

    def setup_persistent_orders(self):
        order_infos = [
            {
                'user': 1
                , 'date': '2024-06-01'
            }
            , {
                'user': 1
                , 'date': '2024-07-01'
                , 'delivery_crew': 3
            }
        ]

        order_items = [
            [
                {
                    'menuitem_id': 1
                    , 'quantity': 4
                }
                , {
                    'menuitem_id': 2
                    , 'quantity': 3
                }
                , {
                    'menuitem_id': 3
                    , 'quantity': 5
                }
            ]
            , 
            [
                {
                    'menuitem_id': 1
                    , 'quantity': 5
                }
                , {
                    'menuitem_id': 2
                    , 'quantity': 1
                }
                , {
                    'menuitem_id': 3
                    , 'quantity': 2
                }
            ]
        ]

        self.assertEqual(len(order_infos), len(order_items), 'Please ensure the order_infos and order_items length are the same.')

        for order_info, items in zip(order_infos, order_items):
            order_info['user'] = User.objects.get(pk=order_info['user'])
            order_info['total'] = 0.0
            if 'delivery_crew' in order_info:
                order_info['delivery_crew'] = User.objects.get(pk=order_info['delivery_crew'])
            order_obj = Order.objects.create(**order_info)
            total = 0
            for item in items:
                item_data = MenuItem.objects.get(pk=item['menuitem_id'])
                unit_price = item_data.price
                price = item['quantity'] * unit_price
                total += price
                order_info_dict = {
                    **item
                    , 'price': price
                    , 'unit_price': unit_price
                    , 'order': order_obj
                }

                order_item_obj = OrderItem.objects.create(
                    **order_info_dict
                )
                order_item_obj.save()
            order_obj.total = total
            order_obj.save()

    def client_request(self, endpoint, data=None, method='POST'):
        func_mapping = {
            'GET': self.client.get
            , 'POST': self.client.post
            , 'PUT': self.client.put
            , 'PATCH': self.client.patch
            , 'DELETE': self.client.delete
        }
        assert method.upper() in func_mapping, 'Invalid method (\'{}\'): Please select method in {}'.format(method.upper(), func_mapping.keys())

        data = urllib.parse.urlencode(data) if data is not None else None
        return func_mapping[method.upper()](endpoint, data=data, content_type='application/x-www-form-urlencoded')

    def login_as(self, user):
        login_api_endpoint = self.endpoints['login']
        login_info = {
            'username': user
            , 'password': user
        }
        resp = self.client_request(login_api_endpoint, data=login_info, method='POST')
        self.assertEqual(resp.status_code, HTTP_200_OK, "Account '{}' cannot logged in\n{}".format(user, resp.content))
        self.user = user
        self.user_id = User.objects.get(username=user).id

        content_data = json.loads(resp.content)
        self.client.credentials(HTTP_AUTHORIZATION = 'Token {}'.format(content_data.get('auth_token')))

    def create_menu_categories(self):
        new_category_data = [
            {'title': 'Fruits', 'slug': 'Fruits'}
            , {'title': 'Fish', 'slug': 'Fish'}
        ]

        endpoint = self.endpoints['category']

        for data in new_category_data:
            resp = self.client_request(endpoint, data=data, method='POST')
            self.assertEqual(resp.status_code, HTTP_201_CREATED, 'Category \'{}\' unable to be created via API'.format(data))

    def create_menu_items(self):
        endpoint = self.endpoints['menu-items']
        data = [
            {
                "title": "Ice Lemonade"
                , "price": 4.10
                , "featured": False
                , "category": "Beverage" 
            }
        ]

        for item in data:
            resp = self.client_request(endpoint, data=item, method="POST")
            self.assertEqual(resp.status_code, HTTP_201_CREATED, 'Menu-item is unable to be created. {}'.format(resp.content))

    def get_manager_group(self):
        endpoint = self.endpoints['manager-group']
        resp = self.client_request(endpoint, method='GET')

        self.assertEqual(resp.status_code, HTTP_200_OK, 'Cannot get manager group')

    def assign_and_remove_to_manager_group(self):
        endpoint = self.endpoints['manager-group']

        non_manager = User.objects.exclude(groups__name='Manager')

        for user in non_manager:
            resp = self.client_request(endpoint, data= {'userId': user.id}, method='POST')
            self.assertEqual(resp.status_code, HTTP_200_OK, 'unable to assign user \'{}\' to manager group'.format(user.username))

            resp = self.client.delete(endpoint + '/{}'.format(user.id))
            self.assertEqual(resp.status_code, HTTP_200_OK, 'unable to remove user \'{}\' to manager group'.format(user.username))

    def update_item_of_the_day(self):
        endpoint = self.endpoints['menu-items']

        selected_data = {
            "title": "Carbonara"
            , "price": 14.90
            , "featured": False
            , "category": "Main"
        }

        data = MenuItemSerializer(data=selected_data)

        for method in ("PUT", "PATCH"):
            title = selected_data['title']
            price = selected_data['price']
            menu_item_id = MenuItem.objects.get(title=title, price=price).id

            resp = self.client_request(endpoint + '/{}'.format(menu_item_id), data=selected_data, method=method)
            self.assertEqual(resp.status_code, HTTP_200_OK, 'Unable to update item of the day via {}'.format(method))
            self.assertEqual(MenuItem.objects.get(title=title, price=price).featured, selected_data['featured'], 'featured is not updated correctly')
            selected_data['featured'] = not selected_data['featured']

    def assign_delivery_crew_to_orders(self):
        endpoint = self.endpoints['orders']
        delivery_crew = User.objects.filter(groups__name = 'Delivery Crew').first()

        order = Order.objects.first()

        for method in ('PUT', 'PATCH'):
            resp = self.client_request(endpoint + '/{}'.format(order.id), data={'order.delivery_crew_id': delivery_crew.id}, method=method)

            self.assertEqual(resp.status_code, HTTP_200_OK
            , 'Unable to assign delivery crew \'{}\' to order id \'{}\' using \'{}\' method\n{}'.format(delivery_crew.id, order.id, method, resp.content))

    def view_menu_items(self):
        endpoint = self.endpoints['menu-items']
        resp = self.client_request(endpoint, method="GET")

        self.assertEqual(resp.status_code, HTTP_200_OK, "Unable to view menu items")

    def view_categories(self):
        endpoint = self.endpoints['category']

        resp = self.client_request(endpoint, method='GET')

        self.assertEqual(resp.status_code, HTTP_200_OK, 'Unable to view categories')

    def view_orders(self):
        endpoint = self.endpoints['orders']

        resp = self.client_request(endpoint, method='GET')

        self.assertEqual(resp.status_code, HTTP_200_OK, 'Unable to view orders')

    def view_carts(self):
        endpoint = self.endpoints['cart']

        resp = self.client_request(endpoint, method="GET")

        self.assertEqual(resp.status_code, HTTP_200_OK, 'Unable to view carts')

    def add_to_cart(self):
        cart_info = [
            {
                'menuitem_id': 1
                , 'quantity': 3
            }
            , {
                'menuitem_id': 2
                , 'quantity': 4
            }
            , {
                'menuitem_id': 1
                , 'quantity': 4
            }
        ]
        endpoint = self.endpoints['cart']
        for item in cart_info:
            resp = self.client_request(endpoint, data=item, method='POST')
            self.assertIn(resp.status_code, (HTTP_201_CREATED, HTTP_200_OK), 'Unable to add items into carts. {}'.format(resp.content))

    def clear_cart(self):
        endpoint = self.endpoints['cart']

        resp = self.client_request(endpoint, method="DELETE")

        self.assertEqual(resp.status_code, HTTP_200_OK, 'Unable to clear cart')

    def place_order(self):
        endpoint = self.endpoints['orders']

        resp = self.client_request(endpoint, method="POST")

        self.assertEqual(resp.status_code, HTTP_201_CREATED, 'Unable to place order')

    def update_order_delivery_status(self):
        order_info = Order.objects.filter(delivery_crew__id = self.user_id).first()

        order_id = order_info.id

        endpoint = self.endpoints['orders']

        for method in ("PUT", "PATCH"):

            new_status = not Order.objects.get(pk=order_id).status

            resp = self.client_request(endpoint+"/{}".format(order_id), data={'order.status': new_status}, method=method)

            self.assertEqual(resp.status_code, HTTP_200_OK, 'Unable to update order via {} method'.format(method))
            status = Order.objects.get(pk = order_id).status

            self.assertEqual(status, new_status, 'Status code is okay. But delivery status of order is not updated.{}'.format(resp.content))

    def test_register(self):
        api_endpoint = self.endpoints['register']

        test_account = 'test_register'

        data = {
            'username': test_account
            , 'password': 'test_password'
        }
        resp = self.client_request(api_endpoint, data=data, method='POST')

        self.assertEqual(resp.status_code, HTTP_201_CREATED, "Account '{}' cannot be registered".format(test_account))

        login_api = '/api/users/login'

        resp = self.client_request(login_api, data=data, method='POST')

        self.assertEqual(resp.status_code, HTTP_200_OK, "API-created Account '{}' cannot be logged in".format(test_account))

        user_account = User.objects.get(username=test_account)
        self.assertEqual(user_account.groups.filter(name='Customer').exists(), True, 'Newly Created account is not in Customer group')

    def test_login_api(self):
        api_endpoint = self.endpoints['login']
        accounts = ['Admin'] + self.all_groups

        for account in self.all_groups:
            data = {
                'username': account
                , 'password': account
            }
            resp = self.client_request(api_endpoint, data=data, method='POST')
            
            self.assertEqual(resp.status_code, HTTP_200_OK, "Account '{}' cannot logged in\n{}".format(account, resp.content))
    
    def test_nonlogin(self):
        url = self.endpoints['menu-items']
        expected_status_code = HTTP_401_UNAUTHORIZED
        resp = self.client_request(url, method="GET")

        self.assertEqual(resp.status_code, expected_status_code, 'Unauthorized user can access \'{}\'. (Expected Status Code: \'{}\', Obtained Status Code: \'{}\')'.format(url, expected_status_code, resp.status_code))

        url = url + '/1'
        expected_status_code = HTTP_401_UNAUTHORIZED
        resp = self.client_request(url, method="GET")

        self.assertEqual( resp.status_code, expected_status_code, 'Unauthorized user can access \'{}\'. (Expected Status Code: \'{}\', Obtained Status Code: \'{}\')'.format(url, expected_status_code, resp.status_code))

    def test_admin_rights(self):
        user = 'Admin'

        self.login_as(user)

        self.view_menu_items()
        self.view_categories()
        self.view_orders()
        self.create_menu_categories()
        self.create_menu_items()
        self.get_manager_group()
        self.assign_and_remove_to_manager_group()

    def test_manager_rights(self):
        user = 'Manager'
        self.login_as(user)

        self.view_menu_items()
        self.view_orders()
        self.view_categories()
        self.update_item_of_the_day()
        self.assign_delivery_crew_to_orders()        
    
    def test_delivery_crew_rights(self):
        user = 'Delivery Crew'
        self.login_as(user)

        self.view_orders()
        self.update_order_delivery_status()
        self.view_menu_items()

    def test_customer_rights(self):
        user = 'Customer'

        self.login_as(user)
        self.view_menu_items()
        self.view_carts()
        self.add_to_cart()
        self.place_order()

        self.clear_cart()