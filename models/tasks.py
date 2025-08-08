import json
from django.db import transaction
from .models import PartCategory, PartUnified, CarsModel, CarBrandsModel
from products.choices.car_data import CAR_MAP, BRAND_DISPLAY_NAMES, CATEGORY_KEYWORDS, CATEGORY_PATHS
from core.logs import CustomLogger
logger = CustomLogger()

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
    try:
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
                        # حالا ۳ مقدار داریم: کد انگلیسی ماشین، نام فارسی ماشین، کد برند
                        car_code_en, car_name_fa, brand_code_en = car_info

                        # ساخت یا بازیابی برند ماشین با نام فارسی
                        brand, _ = CarBrandsModel.objects.get_or_create(
                            name=brand_code_en,
                            defaults={'display_name': BRAND_DISPLAY_NAMES.get(brand_code_en, brand_code_en)}
                        )

                        # ساخت یا بازیابی ماشین با برند مرتبط
                        car, _ = CarsModel.objects.get_or_create(
                            code=car_code_en,
                            defaults={
                                'name': car_name_fa,
                                'brand': brand,
                                'slug': car_code_en,
                            }
                        )
                        car_objects.append(car)
                    else:
                        # اگر در مپ نبود، فقط به صورت نام وارد شود (بدون برند)
                        car_code_slug = car_name_fa.replace(" ", "-")
                        car, _ = CarsModel.objects.get_or_create(
                            code=car_code_slug,
                            defaults={
                                'name': car_name_fa,
                                'slug': car_code_slug,
                                'brand': None,
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

    except Exception as e:
        logger.log(
                module_name="products.tasks",
                class_name="process_uploaded_json",
                message="Error when manage daata into db",
                error=str(e)
            )

def manage_tmkb2b(json_path):
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data_list = json.load(f)
    
    for item in data_list:
        commercial_code = item.get('tegaratCode') or item.get('commercial_code') 
        if not commercial_code:
            continue
        
        try:
            obj = PartUnified.objects.get(commercial_code=commercial_code)
            obj.name = item.get('name', obj.name)
            obj.price = item.get('price', obj.price)
            obj.save()
        except PartUnified.DoesNotExist:
            try:
                obj = PartUnified.objects.create(
                    name = item.get('name', ''),
                    commercial_code = commercial_code,
                    price = item.get('price', 0),
                    internal_code = item.get('ekhtesasiCode', ''), 
                )
                obj.save()
            except Exception as e:
                logger.log(
                    module_name="products.tasks",
                    class_name="manage_tmkb2b",
                    message="Error when creating product into db",
                    error=str(e)
                )
        except Exception as e:
            logger.log(
                module_name="products.tasks",
                class_name="manage_tmkb2b",
                message="Error when manage data into db",
                error=str(e)
            )
