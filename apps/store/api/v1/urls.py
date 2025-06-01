from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.store.api.v1.views import CreateUpdateDestroyStoreView, StoreListView, BaseStoreDetailView, MenuViewSet, MenuItemViewSet, CuisineViewSet, ModifierViewSet, CategoryViewSet, ModifierGroupViewSet


router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("create-store/", CreateUpdateDestroyStoreView.as_view(), name="create_store"),
    path("stores/", StoreListView.as_view(), name="store_list"),
    path("store/<int:pk>/", BaseStoreDetailView.as_view(), name="store_detail"),
    path("create-menu/", MenuViewSet.as_view(), name='create_menu'),
    path("menu/", MenuViewSet.as_view(), name="menu_list"),
    path("menu/<int:pk>/", MenuViewSet.as_view(), name="menu_detail"),
    path("menu-items/", MenuItemViewSet.as_view()),
    path("menu-items/<int:pk>/", MenuItemViewSet.as_view(), name="menu_item_detail"),
    path("cuisines/", CuisineViewSet.as_view(), name="cuisine_list"),
    path("cuisines/<int:pk>/", CuisineViewSet.as_view(), name="cuisine_detail"),
    path("categories/", CategoryViewSet.as_view(), name="category_list"),
    path("categories/<int:pk>/", CategoryViewSet.as_view(), name="category_detail"),
    path("modifiers/", ModifierViewSet.as_view(), name="modifier_list"),
    path("modifiers/<int:pk>/", ModifierViewSet.as_view(), name="modifier_detail"),
    path("modifier-groups/", ModifierGroupViewSet.as_view(), name="modifier_group_list"),
    path("modifier-groups/<int:pk>/", ModifierGroupViewSet.as_view(), name="modifier_group_detail"),   
]
