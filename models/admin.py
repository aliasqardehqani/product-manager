from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import CarBrandsModel, CarsModel, PartCategory, PartUnified


@admin.register(CarBrandsModel)
class CarBrandsAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'created_at', 'updated_time')
    search_fields = ('display_name', 'name')
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CarsModel)
class CarsAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'brand', 'created_at', 'updated_time')
    list_filter = ('brand',)
    search_fields = ('name', 'code')
    prepopulated_fields = {"slug": ("code",)}


@admin.register(PartCategory)
class PartCategoryAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = ('tree_actions', 'indented_title', 'description')
    list_display_links = ('indented_title',)


@admin.register(PartUnified)
class PartUnifiedAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'commercial_code', 'price', 'part_type', 'turnover', 'inventory', 'has_warranty'
    )
    list_filter = ('part_type', 'turnover', 'has_warranty')
    search_fields = ('name', 'internal_code', 'commercial_code', 'category_title')
    filter_horizontal = ('cars',)
    readonly_fields = ('category_title', 'category_url', 'category_description')
