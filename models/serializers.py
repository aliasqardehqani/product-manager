from rest_framework import serializers
from .models import CarBrandsModel, CarsModel, PartUnified, PartCategory

class JSONUploadSerializer(serializers.Serializer):
    file = serializers.FileField()



class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrandsModel
        fields = ['id', 'name', 'display_name']


class CarSerializer(serializers.ModelSerializer):
    brand = CarBrandSerializer()

    class Meta:
        model = CarsModel
        fields = ['id', 'code', 'name', 'brand']

# -----------------------------------------------------------------------
class SimpleCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarsModel
        fields = ['id', 'code', 'name']


class CarBrandWithCarsSerializer(serializers.ModelSerializer):
    cars = SimpleCarSerializer(many=True)

    class Meta:
        model = CarBrandsModel
        fields = ['id', 'name', 'display_name', 'cars']

        
# ------------------------------------------------------------------------
        
class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartUnified
        fields = ['id', 'name', 'price', "image_urls"]

class PartCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartCategory
        fields = ['name']

class PartUnifiedSerializer(serializers.ModelSerializer):
    car_names = serializers.SerializerMethodField()
    inventory_warning = serializers.SerializerMethodField()  # این باید حتما باشه
    category = PartCategorySerializer()

    class Meta:
        model = PartUnified
        fields = [
            'id', 'name', 'internal_code', 'commercial_code', 'price',
            'description', 'image_urls', 'part_type',
            'car_names', 'category', 'turnover', 'inventory',
            'inventory_warning', 'has_warranty', 'warranty_name' 
        ]

    def get_car_names(self, obj):
        return [car.name for car in obj.cars.all()]

    def get_inventory_warning(self, obj):
        return obj.inventory_warning

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartCategory
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartUnified
        fields = ['id', 'name', 'category', 'price', 'cars', 'image_urls', 'part_type', 'turnover', 'inventory', 'has_warranty']
