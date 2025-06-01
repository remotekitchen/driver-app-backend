from apps.store.models import Store, Address, StoreOperatingHour, Cuisine, Category, Menu, MenuItem, Modifier, ModifierGroup
from rest_framework import serializers
from django.db import transaction


class StoreOperatingHourSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = StoreOperatingHour
        fields = ['id', 'day_of_week', 'day_of_week_display', 'open_time', 'close_time']

class BaseAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        
    
        
class BaseStoreSerializer(serializers.ModelSerializer):
    address = BaseAddressSerializer()
    operating_hours = StoreOperatingHourSerializer(many=True, required=False)
    is_store_open = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = '__all__'

    def get_is_store_open(self, obj):
        return obj.is_store_open

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        hours_data = validated_data.pop('operating_hours', [])
        address = Address.objects.create(**address_data)
        store = Store.objects.create(address=address, **validated_data)

        for hour in hours_data:
            StoreOperatingHour.objects.create(store=store, **hour)

        return store

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        hours_data = validated_data.pop('operating_hours', None)

        if address_data:
            for attr, value in address_data.items():
                setattr(instance.address, attr, value)
            instance.address.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if hours_data is not None:
            instance.operating_hours.all().delete()
            for hour in hours_data:
                StoreOperatingHour.objects.create(store=instance, **hour)

        return instance
    
    
class BaseCuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = '__all__'

class BaseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


        
class BaseModifierGroupSerializer(serializers.ModelSerializer):
    modifier = serializers.PrimaryKeyRelatedField(many=True, queryset=Modifier.objects.all(), required=False)
    class Meta:
        model = ModifierGroup
        fields = '__all__'
        
class BaseModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = '__all__'
        
class BaseMenuSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Menu
        fields = '__all__'
        

      
class BaseMenuItemSerializer(serializers.ModelSerializer):
    modifier_groups = BaseModifierGroupSerializer(many=True, read_only=True)
    menu_name = serializers.CharField(source='menu.name', read_only=True)
    class Meta:
        model = MenuItem
        fields = '__all__'
        
    def get_menu_name(self, obj):
        return obj.menu.name if obj.menu else None
    