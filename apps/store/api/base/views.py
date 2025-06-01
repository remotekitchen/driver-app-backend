from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from apps.core.permissions import IsOwnerRoleOrReadOnly
from apps.store.models import Store, Menu, MenuItem, Category, Cuisine, Modifier, ModifierGroup
from apps.store.api.base.serializers import BaseStoreSerializer
from apps.store.api.v1.serializers import MenuSerializer, MenuItemSerializer, CategorySerializer, CuisineSerializer, ModifierSerializer, ModifierGroupSerializer
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

class BaseCreateUpdateDestroyStoreView(APIView):
    serializer_class = BaseStoreSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerRoleOrReadOnly]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, pk=None, *args, **kwargs):
        try:
            store = Store.objects.get(pk=pk)
        except Store.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, store)

        serializer = self.serializer_class(store, data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk=None, *args, **kwargs):
        try:
            store = Store.objects.get(pk=pk)
        except Store.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, store)

        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseStoreListView(ListAPIView):
    queryset = Store.objects.all()
    serializer_class = BaseStoreSerializer
    
class BaseStoreDetailView(RetrieveAPIView):
    queryset = Store.objects.all()
    serializer_class = BaseStoreSerializer
    
    
class BaseMenuViewSet(APIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerRoleOrReadOnly()]
      
    def get(self, request, *args, **kwargs):
        menus = self.queryset.all()
        serializer = self.serializer_class(menus, many=True)
        return Response(serializer.data)
      
    def post(self, request, *args, **kwargs):
        self.check_permissions(request)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.validated_data.get("store")
        if store.owner != request.user:
            raise PermissionDenied("You do not have permission to create a menu for this store.")
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def patch(self, request, pk=None, *args, **kwargs):
        try:
            menu = self.queryset.get(pk=pk)
        except Menu.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, menu)

        serializer = self.serializer_class(menu, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        menu = serializer.save()
        return Response(serializer.data)
      
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            menu = self.queryset.get(pk=pk)
        except Menu.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, menu)

        menu.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BaseMenuItemViewSet(APIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get(self, request, *args, **kwargs):
        menu_items = self.queryset.all()
        serializer = self.serializer_class(menu_items, many=True)
        return Response(serializer.data)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        menu = serializer.validated_data.get("menu")
        if menu.store.owner != request.user:
            raise PermissionDenied("You do not have permission to create a menu item for this store.")
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
      
    def patch(self, request, pk=None, *args, **kwargs):
        try:
            menu_item = self.queryset.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, menu_item)

        serializer = self.serializer_class(menu_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        menu_item = serializer.save()
        return Response(serializer.data)
      
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            menu_item = self.queryset.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, menu_item)

        menu_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    

class BaseCategoryViewSet(APIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerRoleOrReadOnly()]

    def get(self, request, *args, **kwargs):
        categories = self.queryset.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        self.check_permissions(request)  # Ensure permission checks are executed
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.validated_data.get("store")
        if store.owner != request.user:
            raise PermissionDenied("You do not have permission to create a category for this store.")
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None, *args, **kwargs):
        try:
            category = self.queryset.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, category)

        serializer = self.serializer_class(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk=None, *args, **kwargs):
        try:
            category = self.queryset.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, category)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        

class BaseCuisineViewSet(APIView):
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    
    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerRoleOrReadOnly()]
      
    def get(self, request, *args, **kwargs):
        cuisines = self.queryset.all()
        serializer = self.serializer_class(cuisines, many=True)
        return Response(serializer.data)
      
    def post(self, request, *args, **kwargs):
        self.check_permissions(request)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.validated_data.get("store")
        if store.owner != request.user:
            raise PermissionDenied("You do not have permission to create a cuisine for this store.")
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
      
    def patch(self, request, pk=None, *args, **kwargs):
        try:
            cuisine = self.queryset.get(pk=pk)
        except Cuisine.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, cuisine)

        serializer = self.serializer_class(cuisine, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        cuisine = serializer.save()
        return Response(serializer.data)
      
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            cuisine = self.queryset.get(pk=pk)
        except Cuisine.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, cuisine)

        cuisine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
      
class BaseModifierViewSet(APIView):
    queryset = Modifier.objects.all()
    serializer_class = ModifierSerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerRoleOrReadOnly()]

    def get(self, request, *args, **kwargs):
        modifiers = self.queryset.all()
        serializer = self.serializer_class(modifiers, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        self.check_permissions(request)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None, *args, **kwargs):
        try:
            modifier = self.queryset.get(pk=pk)
        except Modifier.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, modifier)
        serializer = self.serializer_class(modifier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        modifier = serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk=None, *args, **kwargs):
        try:
            modifier = self.queryset.get(pk=pk)
        except Modifier.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, modifier)
        modifier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseModifierGroupViewSet(APIView):
    queryset = ModifierGroup.objects.all()
    serializer_class = ModifierGroupSerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerRoleOrReadOnly()]

    def get(self, request, *args, **kwargs):
        groups = self.queryset.all()
        serializer = self.serializer_class(groups, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        self.check_permissions(request)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        menu_item = serializer.validated_data.get("menu_item")
        if menu_item.menu.store.owner != request.user:
            raise PermissionDenied("You do not have permission to create this modifier group.")

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None, *args, **kwargs):
        try:
            group = self.queryset.get(pk=pk)
        except ModifierGroup.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, group)
        serializer = self.serializer_class(group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk=None, *args, **kwargs):
        try:
            group = self.queryset.get(pk=pk)
        except ModifierGroup.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, group)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
