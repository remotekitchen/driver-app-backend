import math

import googlemaps
from decouple import config
from django.contrib.auth import get_user_model
from django.db.models import ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import ACos, Cos, Radians, Sin
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.api.base.serializers import (
    CheckAddressSerializer,
    DeliveryCreateSerializer,
    DeliveryGETSerializer,
)
from apps.billing.models import Delivery, DeliveryFee

gmaps = googlemaps.Client(key=config("GOOGLE_MAP_KEY"))
User = get_user_model()


class BaseCreateDeliveryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = DeliveryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        instance = serializer.instance
        drop_address = f"{instance.drop_off_address.street_address} {instance.drop_off_address.city} {instance.drop_off_address.state} {instance.drop_off_address.postal_code} {instance.drop_off_address.country} "

        drop_off_pointer = self.get_lat(drop_address)
        distance = self.get_distance_between_coords(
            drop_off_pointer.get("lat"),
            drop_off_pointer.get("lng"),
            instance.pickup_latitude,
            instance.pickup_longitude,
        )

        if distance > 10:
            return Response(
                "We can not deliver to this address!",
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver = self.assign_driver_based_on_location(
            instance.pickup_latitude, instance.pickup_longitude
        )

        fees = self.calculate_fees(distance)

        instance.drop_off_latitude = drop_off_pointer.get("lat")
        instance.drop_off_longitude = drop_off_pointer.get("lng")
        instance.distance = distance
        instance.fees = fees
        instance.driver = driver
        instance.status = Delivery.STATUS_TYPE.DRIVER_ASSIGNED
        instance.save()

        sr = DeliveryGETSerializer(instance)
        return Response(sr.data)

    def get_lat(self, address):
        try:
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0].get("geometry", {}).get("location", {})
                lat = location.get("lat")
                lng = location.get("lng")

                if lat is not None and lng is not None:
                    return {"lat": lat, "lng": lng}
            return None

        except googlemaps.exceptions.ApiError as e:
            print(f"Google Maps API error: {e}")
        except googlemaps.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
        except googlemaps.exceptions.TransportError as e:
            print(f"Network-related error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        return None

    def get_distance_between_coords(self, lat1, lng1, lat2, lng2):
        origins = [(lat1, lng1)]
        destinations = [(lat2, lng2)]

        result = gmaps.distance_matrix(origins, destinations, mode="driving")

        try:
            distance = result["rows"][0]["elements"][0]["distance"][
                "value"
            ]  # in meters
            return distance / 1000  # convert to kilometers
        except (IndexError, KeyError):
            return None

    def assign_driver_based_on_location(self, lat, lng):
        earth_radius_km = 6371
        nearby_drivers = (
            User.objects.filter()
            .annotate(
                distance=ExpressionWrapper(
                    earth_radius_km
                    * ACos(
                        Cos(Radians(lat))
                        * Cos(Radians(F("latitude")))
                        * Cos(Radians(F("longitude")) - Radians(lng))
                        + Sin(Radians(lat)) * Sin(Radians(F("latitude")))
                    ),
                    output_field=FloatField(),
                )
            )
            .filter(~Q(distance__isnull=True))
            .order_by("distance")
        )

        if nearby_drivers.exists():
            return nearby_drivers.first()
        return None

    def calculate_fees(self, distance):
        fee_per_km = (
            DeliveryFee.objects.last().per_km if DeliveryFee.objects.exists() else 10
        )

        return float("{0:.2f}".format(distance * fee_per_km))


class BaseCheckAddressAPIView(BaseCreateDeliveryAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = CheckAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data.copy()

        drop_address = f"{data.get("drop_off_address").get("street_address")} {data.get("drop_off_address").get("city")} {data.get("drop_off_address").get("state")} {data.get("drop_off_address").get("postal_code")} {data.get("drop_off_address").get("country")} "

        drop_off_pointer = self.get_lat(drop_address)

        distance = self.get_distance_between_coords(
            drop_off_pointer.get("lat"),
            drop_off_pointer.get("lng"),
            data.get("pickup_latitude"),
            data.get("pickup_longitude"),
        )

        if distance > 10:
            return Response(
                "We can not deliver to this address!",
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver = self.assign_driver_based_on_location(
            data.get("pickup_latitude"), data.get("pickup_longitude")
        )

        if not driver:
            return Response(
                "We can not deliver to this address!",
                status=status.HTTP_400_BAD_REQUEST,
            )

        data.pop("driver")
        fees = self.calculate_fees(distance)

        data["distance"] = distance
        data["fees"] = fees

        return Response(data)
