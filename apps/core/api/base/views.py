from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.core.api.base.serializers import BaseAddressSerializer
from apps.core.models import Address
from rest_framework.permissions import IsAuthenticated


class BaseAddressApiView(APIView):
    """Handles listing and creating addresses."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Retrieve all addresses."""
        addresses = Address.objects.all()
        serializer = BaseAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Create a new address."""
        serializer = BaseAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseAddressDetailApiView(APIView):
    permission_classes = [IsAuthenticated]
    """Handles retrieving, updating, and deleting a specific address."""

    def get_object(self, pk):
        """Retrieve a single address or return 404 if not found."""
        return get_object_or_404(Address, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        """Retrieve a single address."""
        address = self.get_object(pk)
        serializer = BaseAddressSerializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk, *args, **kwargs):
        """Partially update an address."""
        address = self.get_object(pk)
        serializer = BaseAddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """Delete an address."""
        address = self.get_object(pk)
        address.delete()
        return Response({"message": "Address deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
