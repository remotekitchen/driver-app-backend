from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.api.base.serializers import DeliveryCreateSerializer


class BaseCreateDeliveryAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = DeliveryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # get latitude and longitude --> pickup and drop off

        # Assign driver based on lat and lon -->

        # get distance -->

        # get fees -->

        # update data base

        # send response to client --> chatchefs

        return Response(serializer.data)
