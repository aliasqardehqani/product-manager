import json
from django.db import transaction
from .models import PartCategory, PartUnified, CarsModel, CarBrandsModel
from models.choices.car_data import CAR_MAP, BRAND_DISPLAY_NAMES, CATEGORY_KEYWORDS, CATEGORY_PATHS


def find_category_path(title):
    """
    پیدا کردن مسیر دسته‌بندی از CATEGORY_KEYWORDS و CATEGORY_PATHS بر اساس title داده شده
    """
    for cat_key, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return CATEGORY_PATHS.get(cat_key, ["لوازم یدکی"])  # مسیر پیش‌فرض
    return ["لوازم یدکی"]  # مسیر پیش‌فرض اگر پیدا نشد


def get_or_create_category_hierarchy(path_list):
    """
    ایجاد سلسله‌مراتب دسته‌بندی بر اساس لیست مسیر
    """
    parent = None
    for name in path_list:
        category, _ = PartCategory.objects.get_or_create(name=name, parent=parent)
        parent = category
    return parent  # دسته‌بندی آخر برگشت داده می‌شود


@transaction.atomic
def process_uploaded_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for category_data in data.get('categories', []):
        # پیدا کردن مسیر دسته‌بندی و ایجاد سلسله‌مراتب
        cat_path = find_category_path(category_data.get('title', ''))
        category = get_or_create_category_hierarchy(cat_path)

        for product in category_data.get('products', []):
            car_objects = []

            for car_name_fa in product.get('cars', []):
                car_info = CAR_MAP.get(car_name_fa)
                if car_info:
                    car_code_en, car_name_fa, brand_code_en = car_info

                    # ساخت یا بازیابی برند ماشین
                    brand, _ = CarBrandsModel.objects.get_or_create(
                        name=brand_code_en,
                        defaults={'display_name': BRAND_DISPLAY_NAMES.get(brand_code_en, brand_code_en)}
                    )

                    # ساخت یا بازیابی ماشین
                    car, _ = CarsModel.objects.get_or_create(
                        name=car_name_fa,
                        defaults={
                            'code': car_code_en,
                            'brand': brand,
                            'slug': car_code_en,
                        }
                    )
                    car_objects.append(car)
                else:
                    # اگر در مپ نبود، فقط به صورت نام وارد شود (بدون برند)
                    car, _ = CarsModel.objects.get_or_create(
                        name=car_name_fa,
                        defaults={
                            'code': car_name_fa.replace(" ", "-"),
                            'slug': car_name_fa.replace(" ", "-"),
                            'brand_id': None,
                        }
                    )
                    car_objects.append(car)

            # تشخیص گارانتی
            has_warranty = "گارانتی" in product['name']
            warranty_name = "گارانتی پلاس" if "گارانتی پلاس" in product['name'] else None

            # ایجاد محصول
            part = PartUnified.objects.create(
                name=product['name'],
                internal_code=product['ekhtesasiCode'],
                commercial_code=product['tegaratCode'],
                price=int(product['price']),
                category=category,
                category_title=category_data['title'],
                category_url=category_data.get('url', ''),
                category_description=category_data.get('description', ''),
                image_urls=category_data.get('images', []),
                has_warranty=has_warranty,
                warranty_name=warranty_name
            )
            part.cars.set(car_objects)
