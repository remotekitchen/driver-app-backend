import math

import googlemaps
import requests
from decouple import config
from django.contrib.auth import get_user_model
from django.db.models import ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import ACos, Cos, Radians, Sin
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.billing.api.base.serializers import (
    BaseCancelDeliverySerializer,
    CheckAddressSerializer,
    DeliveryCreateSerializer,
    DeliveryGETSerializer,
)
from apps.billing.models import Delivery, DeliveryFee
from django.utils.dateparse import parse_date

gmaps = googlemaps.Client(key=config("GOOGLE_MAP_KEY"))
mapbox_api_key = config("MAPBOX_KEY")
User = get_user_model()


class BaseCreateDeliveryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = DeliveryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        

        instance = serializer.instance
        instance.is_new = True  # ✅ MUST be set before save
        drop_address = f"{instance.drop_off_address.street_address} {instance.drop_off_address.city} {instance.drop_off_address.state} {instance.drop_off_address.postal_code} {instance.drop_off_address.country} "
        # drop_address = f"{instance.drop_off_address.drop_address}"
        
        print(drop_address, 'drop_address--------------->')
        print(instance.use_google, 'use_google--------------->')

        drop_off_pointer = self.get_lat(drop_address, instance.use_google)
        distance = self.get_distance_between_coords(
            drop_off_pointer.get("lat"),
            drop_off_pointer.get("lng"),
            instance.pickup_latitude,
            instance.pickup_longitude,
            instance.use_google,
        )

        if distance > 10:
            return Response(
                "We can not deliver to this address!",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # driver = self.assign_driver_based_on_location(
        #     instance.pickup_latitude, instance.pickup_longitude
        # )

        fees = self.calculate_fees(distance)
        
        print(instance.pickup_last_time, 'instance.pickup_last_time--------------->')
        
        # Calculate average speed (in km/h)
        average_speed_kmh = 12.5  # Midpoint of 10-15 km/h range

        # Calculate estimated travel time in minutes
        estimated_travel_time_minutes = (distance / average_speed_kmh) * 60

        instance.drop_off_latitude = drop_off_pointer.get("lat")
        instance.drop_off_longitude = drop_off_pointer.get("lng")
        instance.distance = distance
        instance.fees = fees
        # instance.driver = driver
        instance.assigned = False
        instance.status = Delivery.STATUS_TYPE.WAITING_FOR_DRIVER
        instance.est_delivery_completed_time = instance.pickup_last_time + timedelta(minutes=estimated_travel_time_minutes)
        instance.drop_off_last_time = instance.est_delivery_completed_time
        instance.save()

        sr = DeliveryGETSerializer(instance)
        print(Response(sr.data), 'Response(sr.data)--------------->')
        return Response(sr.data)

    def get_lat(self, address, use_google=True):
        if use_google:
            return self.get_geo_using_gmaps(address)
        return self.get_geo_using_gmaps(address)

    def get_distance_between_coords(self, lat1, lng1, lat2, lng2, use_google=True):
        if use_google:
            return self.get_distance_gmaps(lat1, lng1, lat2, lng2)
        return self.get_distance_gmaps(lat1, lng1, lat2, lng2)

    def get_geo_using_gmaps(self, address):
      
        try:
          # count the api call
            print("API Call")
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

    def get_geo_mapbox(self, address):
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
        params = {"access_token": mapbox_api_key, "limit": 1}
        response = requests.get(url, params=params)
        
        print("API Call mapbox")

        if response.status_code == 200:
            data = response.json()
            if data["features"]:
                lng, lat = data["features"][0]["center"]
                return {"lat": lat, "lng": lng}
            else:
                print("No location found for the given address.")
                return None
        else:
            print(f"Error: {response.status_code}")
            return None

    def get_distance_gmaps(self, lat1, lng1, lat2, lng2):
        origins = [(lat1, lng1)]
        destinations = [(lat2, lng2)]

        result = gmaps.distance_matrix(origins, destinations, mode="driving")

        try:
            distance = result["rows"][0]["elements"][0]["distance"]["value"]
            return distance / 1000
        except (IndexError, KeyError):
            return None

    def get_distance_mapbox(self, lat1, lng1, lat2, lng2):
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{lng1},{lat1};{lng2},{lat2}"
        params = {
            "access_token": mapbox_api_key,
            "geometries": "geojson",
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data["routes"]:
                distance_meters = data["routes"][0]["distance"]
                distance_km = distance_meters / 1000
                return float("{0:.2f}".format(distance_km))
            else:
                print("No route found between the points.")
                return None
        else:
            print(f"Error: {response.status_code}")
            return None

    # def assign_driver_based_on_location(self, lat, lng):
    #     earth_radius_km = 6371
    #     nearby_drivers = (
    #         User.objects.filter()
    #         .annotate(
    #             distance=ExpressionWrapper(
    #                 earth_radius_km
    #                 * ACos(
    #                     Cos(Radians(lat))
    #                     * Cos(Radians(F("latitude")))
    #                     * Cos(Radians(F("longitude")) - Radians(lng))
    #                     + Sin(Radians(lat)) * Sin(Radians(F("latitude")))
    #                 ),
    #                 output_field=FloatField(),
    #             )
    #         )
    #         .filter(~Q(distance__isnull=True))
    #         .order_by("distance")
    #     )

    #     if nearby_drivers.exists():
    #         return nearby_drivers.first()
    #     return None
    def get_nearby_drivers(self, lat, lng, radius_km=5):
        """
        Returns a queryset of drivers within the given radius.
        """
        earth_radius_km = 6371

        nearby_drivers = (
            User.objects.filter(is_driver=True, is_available=True)  # Assuming you track available drivers
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
            .filter(distance__lte=radius_km)  # Get drivers within the radius
            .order_by("distance")
        )

        return nearby_drivers

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
        
        print(data.get("use_google"), 'use_google')

        drop_address = " ".join([
              data.get("drop_off_address", {}).get("street_address", ""),
              data.get("drop_off_address", {}).get("city", ""),
              data.get("drop_off_address", {}).get("state", ""),
              data.get("drop_off_address", {}).get("postal_code", ""),
              data.get("drop_off_address", {}).get("country", ""),
          ]).strip()
        # drop_address = f"{data.get('drop_off_address').get('drop_address')}"

        drop_off_pointer = self.get_lat(drop_address, data.get("use_google"))
        print(drop_off_pointer)

        distance = self.get_distance_between_coords(
            drop_off_pointer.get("lat"),
            drop_off_pointer.get("lng"),
            data.get("pickup_latitude"),
            data.get("pickup_longitude"),
            data.get("use_google"),
        )

        print(distance)

        if distance > 10:
            return Response(
                "We can not deliver to this address!",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # driver = self.assign_driver_based_on_location(
        #     data.get("pickup_latitude"), data.get("pickup_longitude")
        # )

        # if not driver:
        #     return Response(
        #         "We can not deliver to this address!",
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # data.pop("driver")
        fees = self.calculate_fees(distance)

        data["distance"] = distance
        data["fees"] = fees
        data["drop_off_latitude"] = drop_off_pointer.get("lat")
        data["drop_off_longitude"] = drop_off_pointer.get("lng")
        print(data, 'data--------------->')
        return Response(data)


class BaseCancelDeliveryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        sr = BaseCancelDeliverySerializer(data=request.data)
        sr.is_valid(raise_exception=True)
        uid = sr.data.get("uid")
        reason = sr.data.get("reason")

        if not Delivery.objects.filter(uid=uid).exists():
            return Response(
                {"message": "delivery does not exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery = Delivery.objects.get(uid=uid)
        delivery.status = Delivery.STATUS_TYPE.CANCELED
        delivery.reason = reason
        delivery.save()
        return Response({"message": "delivery canceled!"}, status=status.HTTP_200_OK)
      
      
class BaseAvailableOrdersApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns available delivery orders.
        - Admin users can see all available orders.
        - Regular drivers see only orders within a 3 km radius of their location.
        - Only includes orders created within the last 3 hours.
        """
        # Get the time 3 hours ago
        three_hours_ago = timezone.now() - timedelta(hours=3)

        # Check if the user is an admin
        if request.user.role == 'owner':
            # Admin can see all available orders
            available_orders = Delivery.objects.filter(
                status=Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
                created_date__gte=three_hours_ago
            ).order_by("-created_date")  # Show recent orders first

        else:
            # Regular drivers must provide latitude and longitude
            driver_lat = request.GET.get("latitude")
            driver_lng = request.GET.get("longitude")

            if not driver_lat or not driver_lng:
                return Response(
                    {"message": "Latitude and longitude are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                driver_lat = float(driver_lat)
                driver_lng = float(driver_lng)
            except ValueError:
                return Response(
                    {"message": "Invalid latitude or longitude format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Define the search radius (e.g., 3 km)
            search_radius_km = 3
            earth_radius_km = 6371

            # Find available deliveries within the radius and created within the last 3 hours
            available_orders = (
                Delivery.objects.filter(
                    status=Delivery.STATUS_TYPE.WAITING_FOR_DRIVER,
                    created_date__gte=three_hours_ago
                )
                .annotate(
                    calculated_distance=ExpressionWrapper(
                        earth_radius_km
                        * ACos(
                            Cos(Radians(driver_lat))
                            * Cos(Radians(F("pickup_latitude")))
                            * Cos(Radians(F("pickup_longitude")) - Radians(driver_lng))
                            + Sin(Radians(driver_lat)) * Sin(Radians(F("pickup_latitude")))
                        ),
                        output_field=FloatField(),
                    )
                )
                .filter(calculated_distance__lte=search_radius_km)
                .order_by("calculated_distance")
            )

        serializer = DeliveryGETSerializer(available_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

      
      
class BaseAcceptOrderApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, client_id):
        """
        Assigns the order to the first driver who accepts it.
        """
        driver = request.user  # Authenticated driver
        order = Delivery.objects.get(client_id=client_id, assigned=False)
        print(f"Order Type: {type(order)}, Client ID Type: {type(client_id)} --> client_id")

        

        try:
            with transaction.atomic():  # Prevent race conditions
                order = Delivery.objects.select_for_update().get(client_id=client_id, assigned=False)
                

                if order.status != Delivery.STATUS_TYPE.WAITING_FOR_DRIVER:
                    return Response(
                        {"message": "Order is not available."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                order.driver = driver
                order.status = Delivery.STATUS_TYPE.DRIVER_ASSIGNED
                order.assigned = True
                order.save()

                return Response(
                    {"message": "Order assigned successfully!", "order_id": order.id},
                    status=status.HTTP_200_OK,
                )

        except Delivery.DoesNotExist:
            return Response(
                {"message": "Order has already been assigned or does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

class BaseDriverAssignedOrdersApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assigned_orders = Delivery.objects.filter(
            driver=request.user, status=Delivery.STATUS_TYPE.DRIVER_ASSIGNED
        ).order_by("id")
        
        sr = DeliveryGETSerializer(assigned_orders, many=True)
        return Response(sr.data, status=status.HTTP_200_OK)
      
class BaseOrderUpdateRetrieveApiView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, order_id):
        order = Delivery.objects.get(id=order_id, driver=request.user)
        sr = DeliveryGETSerializer(order)
        return Response(sr.data, status=status.HTTP_200_OK)
      
    def patch(self, request, client_id):
        order = get_object_or_404(Delivery, client_id=client_id, driver=request.user)
        serializer = DeliveryGETSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
# get the deliveries that's status are order_picked_up
class BasePickedUpOrdersApiViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Delivery.objects.filter(
            driver=request.user, status=Delivery.STATUS_TYPE.ORDER_PICKED_UP
        ).order_by("id")
        
        print(orders, 'orders--------------->')
        
        sr = DeliveryGETSerializer(orders, many=True)
        return Response(sr.data, status=status.HTTP_200_OK)
      
class BaseDriverOrderApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Delivery.objects.filter(driver=request.user).order_by("id")
        sr = DeliveryGETSerializer(orders, many=True)
        return Response(sr.data, status=status.HTTP_200_OK)
      
class BaseAdminGetAllOrdersApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        orders = Delivery.objects.all().order_by("id")

        # Get query parameters
        date_query = request.query_params.get('date')
        status_query = request.query_params.get('status')
        earnings = request.query_params.get('earnings')
        min_earnings = request.query_params.get('min_earnings')
        max_earnings = request.query_params.get('max_earnings')

        # Apply filters
        if date_query:
            parsed_date = parse_date(date_query)
            if parsed_date:
                # Use __date to filter only by the date part of the pickup_ready_at field
                orders = orders.filter(pickup_ready_at__date=parsed_date)

        if status_query:
            orders = orders.filter(status__icontains=status_query)
            
        if earnings:
            orders = orders.filter(driver_earning=earnings)

        if min_earnings:
            orders = orders.filter(driver_earning__gte=min_earnings)

        if max_earnings:
            orders = orders.filter(driver_earning__lte=max_earnings)

        # Serialize and return the data
        serializer = DeliveryGETSerializer(orders, many=True)
        count = orders.count()
        return Response({"count": count, "orders": serializer.data})
        