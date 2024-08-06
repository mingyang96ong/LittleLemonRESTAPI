# Setup
1. `pipenv install`
2. `pipenv shell`
3. `python manage.py runserver`


## Additional Notes
1. You may run `python manage.py test` to run some of built-in tests

# API Documentation

## Login Related
1. API Endpoint: `/api/users/login`  
Method: `POST`  
Roles: `Any`  
Headers: `Content-Type: application/x-www-form-urlencoded`  
Usage: Requires `username` and `password` in the request body.   Returns `auth_token` if authenticated successfully (`HTTP_200_OK`)
2. API Endpoint: `/api/users/logout`  
Method: `POST`  
Roles: `Authenticated Users`  
Headers: `Authorization: Token <auth_token>`  
Usage: Invalidate `<auth_token>`
3. API Endpoint: `/api/users/`  
Method: `POST`  
Roles: `Any`  
Headers: `Content-Type: application/x-www-form-urlencoded`  
Usage: Requires `username` and `password` in the request body. `email` is optional. Account will be added to `Customer` group by default.

## Menu Items Related
1. API Endpoint: `/api/menu-items`  
    Method: `GET`  
    Roles: `Authenticated Users`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: Get all menu items  

    Method: `POST`  
    Roles: `Admin or Superuser`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Add new menu-items.
2. API Endpoint: `/api/menu-items/<int:pk>`  
    Method: `GET`  
    Roles: `Authenticated Users`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: Get a single menu items of id = `pk`  

    Method: `PUT, PATCH`  
    Roles: `Admin or Superuser`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Update existing menu-item of id = `pk`  

    Method: `DELETE`  
    Roles: `Admin or Superuser`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: Delete existing menu-item of id = `pk`

## Category Related
1. API Endpoint: `/api/category`  
    Method: `GET`  
    Roles: `Authenticated Users`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: Get all categories info

    Method: `POST`  
    Roles: `Admin or Superuser`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`   
    Usage: Add a new category by passing `title` and `slug` in the request body. Ensure `title` is unique as there is a validation check on category title.

2. API Endpoint: `/api/category/<int:pk>`  
    Method: `PUT, PATCH`  
    Roles: `Admin or Superuser`   
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Update existing category with id = `pk`

    Method: `DELETE`  
    Roles: `Admin or Superuser`   
    Headers: `Authorization: Token <auth_token>`  
    Usage: Delete category with id = `pk`

## User Management Related
1. API Endpoint: `/api/groups/manager/users`  
    Method: `GET`  
    Roles: `Admin or Superuser`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View all users that are in `Manager` group   

    Method: `POST`  
    Roles: `Admin or Superuser`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Pass `userId` in the request body to assign user of id=`userId` to `Manager` group 
2. API Endpoint: `/groups/manager/users/<int:userId>`  
Method: `DELETE`  
Roles: `Admin or Superuser`  
Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
Usage: Remove an user of id=`userId` from `Manager` group  
1. API Endpoint: `/api/groups/delivery-crews/users`
    Method: `GET`  
    Roles: `Admin or Superuser`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View all users that are in `Delivery Crew` group   

    Method: `POST`  
    Roles: Admin or Superuser  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Pass `userId` in the request body to assign user of id=`userId` to `Delivery Crew` group
2. API Endpoint: `/groups/delivery-crews/users/<int:userId>`
Method: `DELETE`  
Roles: `Admin or Superuser`  
Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`   
Usage: Remove an user of id=`userId` from `Delivery Crew` group 

## Cart Management Related
1. API Endpoint: `/api/cart/menu-items`
    Method: `GET`  
    Roles: `Customer`  
    Headers: `Authorization: Token <auth_token>`    
    Usage: View all the items in cart of the authenticated user  

    Method: `POST`  
    Roles: `Customer`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Update/add the `menuitem_id` of quantity `quantity` into the user's cart

    Method: `DELETE`  
    Roles: `Customer`  
    Headers: `Authorization: Token <auth_token>`   
    Usage: Clear everything from the authenticated user's cart

## Order Management Related
1. API Endpoint: `/api/orders`  
    Method: `GET`  
    Roles: `Customer`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View all items ordered by current user  

    Method: `GET`  
    Roles: `Manager`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View all items ordered by all users  

    Method: `GET`  
    Roles: `Delivery Crew`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View all ordered items assigned to the current user

    Method: `POST`  
    Roles: `Customer`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: Place order on all items in cart of the current user  
2. API Endpoint: `/api/orders/<int:pk>`  
    Method: `GET`  
    Roles: `Customer`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View items with order id=`pk` ordered by current user  

    Method: `GET`  
    Roles: `Manager or Admin`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View items with order id=`pk`    

    Method: `GET`  
    Roles: `Delivery Crew`  
    Headers: `Authorization: Token <auth_token>`  
    Usage: View items with order id=`pk` if the order is assigned to the current user

    Method: `PUT, PATCH`  
    Roles: `Manager or Admin`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`  
    Usage: Pass the assigned delivery crew by `order.delivery_crew_id` in request body to update the delivery crew of the order with id = `pk`

    Method: `PUT, PATCH`  
    Roles: `Delivery Crew`  
    Headers: `Content-Type: application/x-www-form-urlencoded; Authorization: Token <auth_token>`   
    Usage: Pass the assigned delivery crew by `order.status` in request body to update the delivery status of the order with id = `pk`