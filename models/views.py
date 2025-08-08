import json
import os
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination

from .serializers import (
    CarBrandWithCarsSerializer, 
    PartSerializer, 
    PartUnifiedSerializer, 
    JSONUploadSerializer,
    CategorySerializer, 
    ProductSerializer)
from .models import PartUnified, CarBrandsModel, CarsModel, PartCategory
from products.choices.car_data import CAR_MAP, BRAND_DISPLAY_NAMES, CAR_CHOICES, CATEGORY_KEYWORDS, CATEGORY_PATHS
from .tasks import process_uploaded_json, manage_tmkb2b

from core.logs import CustomLogger
logger = CustomLogger()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100



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

                if file_obj.name == "allData.json":
                    manage_tmkb2b(save_path)
                elif file_obj.name == "final_output":
                    process_uploaded_json(save_path)
                else:
                    pass
                
                if os.path.exists(save_path):
                    os.remove(save_path)

                return Response({
                    "message": "File uploaded and processed successfully",
                    "file_path": save_path
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="JSONUploadAPIView",
                message="Error from manage data into db ",
                error=str(e)
            )
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            serializer = PartUnifiedSerializer(part)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartUnified.DoesNotExist:
            return Response({'error': 'Part not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid ID format.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="PartDetailAPIView",
                message="Error get product all list",
                error=str(e)
            )

# -------------------------------------------------------------------------------------
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

class CategoryListAPIView(APIView):
    def get(self, request):
        try:
            categories = PartCategory.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="CategoryListAPIView",
                message="Error from list of category",
                error=str(e)
            )
            return Response({"error": "Category have error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductByCategoryAPIView(APIView):
    def post(self, request):
        try:
            category_id = request.data.get('id')
            if not category_id:
                return Response({"error": "Category ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                category = PartCategory.objects.get(id=category_id)
            except PartCategory.DoesNotExist:
                return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

            products = PartUnified.objects.filter(category=category).order_by('id')

            # get page and page_size from body with defaults
            page_number = request.data.get('page', 1)
            page_size = request.data.get('page_size', 10)

            paginator = StandardResultsSetPagination()
            paginator.page_size = page_size  # override default page size if provided

            # Manually set query params for paginator, trick to set page number:
            request.query_params._mutable = True  # make query_params mutable temporarily
            request.query_params['page'] = str(page_number)
            request.query_params._mutable = False

            result_page = paginator.paginate_queryset(products, request, view=self)
            serializer = PartUnifiedSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            logger.log(
                module_name="products.views",
                class_name="ProductByCategoryAPIView",
                message="Error from list of category",
                error=str(e)
            )
        