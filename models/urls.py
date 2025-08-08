from django.urls import path
from .views import *
from .views import PartUnifiedListAPIView

urlpatterns = [
    path('list-brands/', ListOfBrandsAPIView.as_view(), name='list-brands'),
    path('list-car-products/', CarPartsListAPIView.as_view(), name='list-car-products'),
    path('all/', AllPartsPaginatedAPIView.as_view(), name='all-parts'),
    path('filter-by-type/', FilterByPartTypeAPIView.as_view(), name='filter-parts-by-type'),
    path('filter-parts/', PartUnifiedListAPIView.as_view(), name='parts-list'),
    path('part/<int:part_id>/', PartDetailAPIView.as_view(), name='part-detail'),
    path('upload-json/', JSONUploadAPIView.as_view(), name='upload-json'),
    path('products_by_category/', ProductByCategoryAPIView.as_view(), name='products-by-category'),
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
]