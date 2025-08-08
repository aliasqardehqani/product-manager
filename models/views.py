import json
import os
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination

from .serializers import CarBrandWithCarsSerializer, PartSerializer, PartUnifiedSerializer, JSONUploadSerializer
from .models import PartUnified, CarBrandsModel, CarsModel, PartCategory
from models.choices.car_data import CAR_MAP, BRAND_DISPLAY_NAMES, CAR_CHOICES, CATEGORY_KEYWORDS, CATEGORY_PATHS
from .tasks import process_uploaded_json 

from core.logs import CustomLogger
logger = CustomLogger()

def assign_category_from_name(part_name: str) -> PartCategory:
    matched_keys = []
    part_name_lower = part_name.lower()

    for key, keywords in CATEGORY_KEYWORDS.items():
        for word in keywords:
            if word.lower() in part_name_lower:
                matched_keys.append(key)
                break

    if not matched_keys:
        category, _ = PartCategory.objects.get_or_create(name="نامشخص", parent=None)
        category.description = f"نامشخص - {part_name}"
        category.save()
        return category
    
    matched_key = matched_keys[0]

    path = CATEGORY_PATHS.get(matched_key, ["نامشخص"])
    parent = None
    category = None

    for node in path:
        category, _ = PartCategory.objects.get_or_create(name=node, parent=parent)
        parent = category

        category.description = f"{category.description or ''}\n{part_name}".strip()
    category.save()

    return category

class JSONUploadAPIView(APIView):
    def post(self, request):
        try:
            serializer = JSONUploadSerializer(data=request.data)
            if serializer.is_valid():
                file_obj = serializer.validated_data['file']
                save_path = os.path.join(settings.BASE_DIR, 'models', 'jsonfile', file_obj.name)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                with open(save_path, 'wb+') as destination:
                    for chunk in file_obj.chunks():
                        destination.write(chunk)

                process_uploaded_json(save_path) 

                return Response({
                    "message": "File uploaded successfully",
                    "file_path": save_path
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # اصلاح: بازگرداندن Response بجای print
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ImportUnifiedPartsAPIView(APIView):
    FA_CAR_TO_DATA = {fa: (code_en, brand_en) for code_en, fa, brand_en in CAR_CHOICES}

    def post(self, request):
        try:
            data = request.data
            # file_path = os.path.join(settings.BASE_DIR, 'final_output.json')
            # with open(file_path, 'r', encoding='utf-8') as f:
            #     data = json.load(f)
            categories = data.get("categories") or []

            for cat in categories:
                category_title = cat.get("title", "")
                category_url = cat.get("url", "")
                category_description = cat.get("description", "")
                image_urls = cat.get("images") or []

                products = cat.get("products") or []
                for product in products:
                    try:
                        internal_code = product.get("tegaratCode")
                        commercial_code = product.get("ekhtesasiCode")
                        name = product.get("name", "").strip()
                        price = product.get("price", 0)
                        description = product.get("description", "")

                        if not internal_code or not commercial_code or not name:
                            continue

                        if PartUnified.objects.filter(name=name).exists():
                            continue  
                        cars = product.get("cars") or []
                        added_car_codes = set()
                        car_objects = []
                        for car_name in cars:
                            if not car_name:
                                continue
                            car_name = car_name.strip()

                            if car_name in self.FA_CAR_TO_DATA:
                                code, brand_code = self.FA_CAR_TO_DATA[car_name]
                                brand_display = BRAND_DISPLAY_NAMES.get(brand_code, brand_code)

                                if code in added_car_codes:
                                    continue

                                brand_obj, _ = CarBrandsModel.objects.get_or_create(
                                    name=brand_code,
                                    defaults={"display_name": brand_display}
                                )

                                car_obj, _ = CarsModel.objects.get_or_create(
                                    code=code,
                                    defaults={"name": car_name, "brand": brand_obj}
                                )

                                car_objects.append(car_obj)
                                added_car_codes.add(code)

                            else:
                                logger.log(
                                    module_name="products.views",
                                    class_name="import_unified_parts_view",
                                    message=f"Unknown car name: {car_name}",
                                    error="car_not_in_choices"
                                )

                        category = assign_category_from_name(name)

                        part = PartUnified.objects.create(
                            name=name,
                            internal_code=internal_code,
                            commercial_code=commercial_code,
                            price=price,
                            description=description,
                            category_title=category_title,
                            category_url=category_url,
                            category_description=category_description,
                            category=category,
                            image_urls=image_urls
                        )

                        part.cars.set(car_objects)
                        part.save()

                    except Exception as e:
                        logger.log(
                            module_name="products.views",
                            class_name="import_unified_parts_view",
                            message="Error processing product",
                            error=str(e)
                        )
                        continue

            return Response({"detail": "Unified import completed successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="import_unified_parts_view",
                message="Error in import",
                error=str(e)
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ListOfBrandsAPIView(APIView):
    def get(self, request):
        try:
            brands = CarBrandsModel.objects.prefetch_related("cars").all()
            serializer = CarBrandWithCarsSerializer(brands, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="ListOfBrandsAPIView",
                message="Error retrieving brands and their cars",
                error=str(e)
            )
            return Response(
                {"error": "An error occurred while fetching brand list."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CarPartsListAPIView(APIView):
    """
    Get paginated list of parts for a given car ID.
    Query Params: car_id, pageNumber, pageSize
    """

    def post(self, request):
        try:
            car_id = request.data.get("car_id")
            page_number = int(request.data.get("page_number", 1))
            page_size = int(request.data.get("page_size", 10))

            if not car_id:
                return Response({"error": "car_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                car = CarsModel.objects.get(id=car_id)
            except CarsModel.DoesNotExist:
                return Response({"error": "Car not found."}, status=status.HTTP_404_NOT_FOUND)

            parts_qs = car.parts.all()
            total_parts = parts_qs.count()

            start = (page_number - 1) * page_size
            end = start + page_size
            paginated_parts = parts_qs[start:end]

            serializer = PartSerializer(paginated_parts, many=True)

            return Response({
                "total_parts": total_parts,
                "page": page_number,
                "page_size": page_size,
                "results": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="CarPartsListAPIView",
                message="Error fetching parts for car",
                error=str(e)
            )
            return Response(
                {"error": "An error occurred while fetching car parts."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

#--------------------------------------------------------------------------------------
class AllPartsPaginatedAPIView(APIView):
    def get(self, request):
        pagenumber = int(request.query_params.get("pagenumber", 1))
        pagesize = int(request.query_params.get("pagesize", 10))
        start = (pagenumber - 1) * pagesize
        end = start + pagesize

        queryset = PartUnified.objects.all()
        serialized = PartUnifiedSerializer(queryset[start:end], many=True)
        return Response({
            "count": queryset.count(),
            "results": serialized.data
        })

class FilterByPartTypeAPIView(APIView):
    '''
    Filter api by :    
    PART_TYPE_CHOICES = (
        ('consumable', 'Consumable'),  
        ('spare', 'Spare Part'),       
    )
    '''
    def post(self, request):
        part_type = request.data.get("part_type")
        pagenumber = int(request.query_params.get("pagenumber", 1))
        pagesize = int(request.query_params.get("pagesize", 10))
        start = (pagenumber - 1) * pagesize
        end = start + pagesize

        if part_type not in dict(PartUnified.PART_TYPE_CHOICES).keys():
            return Response({"error": "Invalid part_type"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = PartUnified.objects.filter(part_type=part_type)
        serialized = PartUnifiedSerializer(queryset[start:end], many=True)
        return Response({
            "count": queryset.count(),
            "results": serialized.data
        })

class PartDetailAPIView(APIView):
    """
    Retrieve a single PartUnified by ID.
    Optimized for large datasets.
    """

    def get(self, request, part_id):
        try:
            # Only fetch necessary fields to optimize DB access
            part = PartUnified.objects.only(
                'id', 'name', 'internal_code', 'commercial_code', 'price', 'part_type'
            ).get(id=part_id)
        except PartUnified.DoesNotExist:
            return Response({'error': 'Part not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid ID format.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PartUnifiedSerializer(part)
        return Response(serializer.data, status=status.HTTP_200_OK)
# -------------------------------------------------------------------------------------


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PartUnifiedListAPIView(generics.ListAPIView):
    '''
        >>> GET /api/parts/
        >>> GET /api/parts/?category_id=3
        >>> GET /api/parts/?page=2
        >>> GET /api/parts/?page=1&page_size=20
        >>> GET /api/parts/?search=شمع
        >>> GET /api/parts/?ordering=price
        >>> GET /api/parts/?ordering=-inventory
    '''
    queryset = PartUnified.objects.all()
    serializer_class = PartUnifiedSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'commercial_code', 'internal_code', 'category_title']
    ordering_fields = ['price', 'inventory']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset