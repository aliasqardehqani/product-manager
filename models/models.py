from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


# ---------------------- Car Brand Model ----------------------
class CarBrandsModel(models.Model):
    name = models.CharField(max_length=100, unique=True)  # English name like "peugeot"
    display_name = models.CharField(max_length=100)       # Persian name like "پژو"
    profile_photo = models.ImageField(upload_to="brand_profiles/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    slug = models.SlugField()


    def str(self):
        return self.display_name



# ---------------------- Car Model ----------------------
class CarsModel(models.Model):
    code = models.CharField(max_length=100, unique=True)  # English slug like "peugeot-206"
    name = models.CharField(max_length=100)               # Persian like "پژو 206"
    brand = models.ForeignKey(CarBrandsModel, on_delete=models.CASCADE, related_name="cars")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="car_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    slug = models.SlugField()
 

    def __str__(self):
        return f"{self.brand.name} - {self.name}"



class PartCategory(MPTTModel):
    name = models.CharField(max_length=255, unique=True)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    description = models.TextField(blank=True, null=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class PartUnified(models.Model):
    PART_TYPE_CHOICES = (
        ('consumable', 'Consumable'),
        ('spare', 'Spare Part'),
    )

    TURNOVER_CHOICES = (
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    )

    name = models.CharField(max_length=255)
    internal_code = models.CharField(max_length=50)
    commercial_code = models.CharField(max_length=50)
    price = models.PositiveIntegerField()
    cars = models.ManyToManyField('CarsModel', related_name="parts")
    description = models.TextField(blank=True, null=True)

    category_title = models.CharField(max_length=255)
    category_url = models.URLField()
    category_description = models.TextField(blank=True, null=True)

    category = models.ForeignKey(
        PartCategory,
        on_delete=models.CASCADE,
        related_name='parts',
        null=True,
        blank=True
    )

    image_urls = models.JSONField(blank=True, null=True, help_text="List of image URLs related to the part category")

    part_type = models.CharField(
        max_length=20,
        choices=PART_TYPE_CHOICES,
        default='spare',
        help_text="Specify whether the part is a consumable item or a spare part"
    )

    turnover = models.CharField(
        max_length=1,
        choices=TURNOVER_CHOICES,
        blank=True,
        null=True,
        help_text="Product turnover category: A, B, C, or D"
    )
    inventory = models.IntegerField(
        default=0,
        help_text="Current inventory count for the part"
    )

    has_warranty = models.BooleanField(
        default=False,
        help_text="Indicates whether the part has a warranty"
    )
    warranty_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the warranty in Persian"
    )

    def __str__(self):
        return f"{self.name} - {self.commercial_code} - Category: {self.category_title}"

