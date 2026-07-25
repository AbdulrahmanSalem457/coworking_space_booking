from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import Space
from .permissions import IsSpaceOwnerOrReadOnly
from .serializers import SpaceSerializer


class SpaceViewSet(viewsets.ModelViewSet):
    """
    list: Browse all active coworking spaces.
    retrieve: View full details for a single space.
    create/update/destroy: Restricted to space owners/staff.
    """

    queryset = Space.objects.filter(is_active=True)
    serializer_class = SpaceSerializer
    permission_classes = [IsSpaceOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["capacity"]
    search_fields = ["name", "description"]
    ordering_fields = ["price_per_hour", "capacity", "created_at"]
    lookup_field = "slug"

    @swagger_auto_schema(operation_summary="List coworking spaces", tags=["Spaces"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve a coworking space", tags=["Spaces"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Create a coworking space", tags=["Spaces"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update a coworking space", tags=["Spaces"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Delete a coworking space", tags=["Spaces"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        method="get",
        operation_summary="Space choices (slug + name)",
        operation_description=(
            "Quick-reference list of every active space — no pagination. "
            "Use the slug value as the `space` field when creating a booking."
        ),
        tags=["Spaces"],
        responses={
            200: openapi.Response(
                description="List of active spaces",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "slug": openapi.Schema(type=openapi.TYPE_STRING, example="creative-hub"),
                            "name": openapi.Schema(type=openapi.TYPE_STRING, example="Creative Hub"),
                        },
                    ),
                ),
            )
        },
    )
    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny], url_path="choices")
    def choices(self, request):
        spaces = Space.objects.filter(is_active=True).values("slug", "name").order_by("name")
        return Response(list(spaces))
