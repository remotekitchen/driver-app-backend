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
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.mail import send_mail
from django.conf import settings

from apps.billing.api.base.serializers import (
    BaseCancelDeliverySerializer,
    CheckAddressSerializer,
    DeliveryCreateSerializer,
    DeliveryGETSerializer,
    DashboardSerializer,
    DeliveryIssueSerializer,
)
from apps.billing.models import Delivery, DeliveryFee, DeliveryIssue
from django.utils.dateparse import parse_date

gmaps = googlemaps.Client(key=config("GOOGLE_MAP_KEY"))
mapbox_api_key = config("MAPBOX_KEY")
User = get_user_model()
from apps.billing.api.base.serializers import BaseDriverSerializer
from django.utils.timezone import now
from django.db.models import Count, Sum
from collections import defaultdict
from django.db.models.functions import TruncDate
from apps.billing.models import DeliveryEarningConfig
from apps.billing.utils.earning_calculation import calculate_driver_earning,calculate_total_driver_earning
from apps.billing.utils.guarantee import OnTimeGuaranteeService
from apps.firebase.utils.fcm_helper import send_push_notification
from apps.core.permissions import IsOwnerRoleOrReadOnly
from apps.firebase.models import TokenFCM


import logging

logger = logging.getLogger(__name__)

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

        if distance > 15:
            return Response(
                "We can not deliver to this address!",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # driver = self.assign_driver_based_on_location(
        #     instance.pickup_latitude, instance.pickup_longitude
        # )

        fees = self.calculate_fees(distance)
        
        print(instance.pickup_last_time, 'instance.pickup_last_time--------------->')
        
        # # Calculate average speed (in km/h)
        # average_speed_kmh = 12.5  # Midpoint of 10-15 km/h range

        # # Calculate estimated travel time in minutes
        # estimated_travel_time_minutes = (distance / average_speed_kmh) * 60

        
        # Load config from DB
        config = DeliveryEarningConfig.objects.first()

         # If config exists, get estimated_time_per_km, else fallback to 3.5
        time_per_km_minutes = config.estimated_time_per_km if config else 3.5

        # Now calculate estimated delivery time based on distance
        estimated_travel_time_minutes = distance * time_per_km_minutes


        instance.drop_off_latitude = drop_off_pointer.get("lat")
        instance.drop_off_longitude = drop_off_pointer.get("lng")
        instance.distance = distance
        instance.fees = fees
        # instance.driver = driver
        instance.assigned = False
        instance.status = Delivery.STATUS_TYPE.WAITING_FOR_DRIVER
        # instance.est_delivery_completed_time = instance.pickup_last_time + timedelta(minutes=estimated_travel_time_minutes)
        instance.est_delivery_completed_time = instance.pickup_last_time 
        instance.drop_off_last_time = instance.est_delivery_completed_time
        
        instance.save()
        

        sr = DeliveryGETSerializer(instance)
        # Add this to print delivery data
        import json
        print("🚚 Delivery Created with Data:")
        print(json.dumps(sr.data, indent=4, default=str))

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
            return calculate_driver_earning(distance)


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

        if distance > 15:
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
      

class BaseDriverCancelDeliveryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, client_id):
        delivery = get_object_or_404(Delivery, client_id=client_id, driver=request.user)

        if delivery.status in [
            Delivery.STATUS_TYPE.ORDER_PICKED_UP,
            Delivery.STATUS_TYPE.ON_THE_WAY
        ]:
            delivery.status = Delivery.STATUS_TYPE.DELIVERY_FAILED
            delivery.cancel_reason = "Driver cancelled during delivery"
            delivery.save()

            # Notify Chatchef
            try:
                requests.post("http://127.0.0.1:8000/api/webhook/v1/raider/", json={
                    "event": "status",
                    "client_id": delivery.client_id,
                    "status": delivery.status,
                    "cancel_reason": delivery.cancel_reason,
                })
            except Exception as e:
                print("Failed to notify Chatchef webhook:", str(e))

            return Response({
                "message": "The delivery man has some issue, you will get full refund."
            })

        # ❌ If not in cancelable status
        return Response({"message": "Cannot cancel at this stage."}, status=400)


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
        print(client_id, 'client_id--------------->')
        order = get_object_or_404(Delivery, client_id=client_id, driver=request.user)
        print(order, 'order--------------->')
        old_status = order.status
        serializer = DeliveryGETSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            updated_instance = serializer.instance  #  This now includes new status and actual_delivery_completed_time

            # If updated to DELIVERY_SUCCESS, check reward eligibility
            if updated_instance.status == Delivery.STATUS_TYPE.DELIVERY_SUCCESS and old_status != Delivery.STATUS_TYPE.DELIVERY_SUCCESS:
                try:
                    logger.info("✅ Call On-Time Guarantee")
                    OnTimeGuaranteeService(updated_instance).run()
                except Exception as e:
                    logger.error(f"❌ On-Time Guarantee failed: {e}")

                earning_result = updated_instance.update_final_earning()
                updated_instance.save()
                print(f"✅ Driver earning updated: {updated_instance.driver_earning} BDT with penalty {earning_result['penalty_percentage']}%")
            
            # ✅ Refresh and return fresh data
            updated_instance.refresh_from_db()
            updated_serializer = DeliveryGETSerializer(updated_instance)
            return Response(updated_serializer.data, status=status.HTTP_200_OK)
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
        orders = Delivery.objects.all().order_by("-created_date")


        # Query params
        date_query = request.query_params.get("date")
        status_query = request.query_params.get("status")
        earnings = request.query_params.get("earnings")
        min_earnings = request.query_params.get("min_earnings")
        max_earnings = request.query_params.get("max_earnings")
        restaurant_id = request.query_params.get("restaurant")
        all_restaurants = request.query_params.get("all_restaurants")

        # Apply filters
        if date_query:
            parsed_date = parse_date(date_query)
            if parsed_date:
                orders = orders.filter(pickup_ready_at__date=parsed_date)

        if status_query:
            orders = orders.filter(status__icontains=status_query)

        if earnings:
            orders = orders.filter(driver_earning=earnings)

        if min_earnings:
            orders = orders.filter(driver_earning__gte=min_earnings)

        if max_earnings:
            orders = orders.filter(driver_earning__lte=max_earnings)

        if restaurant_id and not all_restaurants:
            orders = orders.filter(order__restaurant_id=restaurant_id)

        serializer = DeliveryGETSerializer(orders, many=True)
        return Response({"count": orders.count(), "orders": serializer.data})


class BaseDashboardSalesApiView(APIView):
    def get(self, request):
        # Parse query params with defaults
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        order_type = request.query_params.get('order_type', 'delivery')

        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else now().date()
        except:
            return Response({"error": "Invalid end_date"}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else end_date - timedelta(days=6)
        except:
            return Response({"error": "Invalid start_date"}, status=400)

        current_datetime = now()

        # This week range: last 7 full days from now
        this_week_start = current_datetime - timedelta(days=7)
        this_week_end = current_datetime

        # Previous week range: 7 days before this_week_start
        prev_week_start = this_week_start - timedelta(days=7)
        prev_week_end = this_week_start

        # (Optional) You can print or log these to verify
        print(this_week_start, this_week_end, prev_week_start, prev_week_end, 'Computed time ranges')

        # Greeting
        current_hour = now().hour
        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        admin_name = "Admin"

        # Get drivers dynamically (filter your driver role/group)
        drivers = User.objects.filter(role=User.RoleType.DRIVER) 
        print(drivers, 'drivers--------------->')
        driver_ids = list(drivers.values_list('id', flat=True))
        driver_names = {driver.id: " ".join(filter(None, [driver.first_name, driver.last_name])) for driver in drivers}
        print(driver_names, driver_ids, 'driver_names--------------->')

        # Total deliveries this week by driver
        deliveries_this_week = (
            Delivery.objects.filter(
                driver_id__in=driver_ids,
                actual_delivery_completed_time__range=[this_week_start, this_week_end],
                status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS,
            )
            .values('driver_id')
            .annotate(count=Count('id'))
        )
        deliveries_this_week_map = {item['driver_id']: item['count'] for item in deliveries_this_week}
        
        print(deliveries_this_week_map, 'deliveries_this_week_map--------------->')

        # Total deliveries previous week by driver
        deliveries_prev_week = (
            Delivery.objects.filter(
                driver_id__in=driver_ids,
                actual_delivery_completed_time__date__range=[prev_week_start, prev_week_end],
                status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS,
            )
            .values('driver_id')
            .annotate(count=Count('id'))
        )
        deliveries_prev_week_map = {item['driver_id']: item['count'] for item in deliveries_prev_week}
        
        all_deliveries = (
            Delivery.objects.filter(
                driver_id__in=driver_ids,
                actual_delivery_completed_time__date__range=[start_date, end_date],
                status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS,
            )
            .values('driver_id')
            .annotate(count=Count('id'))
        )
        all_deliveries_map = {item['driver_id']: item['count'] for item in all_deliveries}
        

        # Build driver summary with weekly growth
        driver_summary_list = []
        total_deliveries_all = 0
        failed_deliveries_all = 0
        total_deliveries_prev_all = 0
        for driver in drivers:
            all_deliveries_count = all_deliveries_map.get(driver.id, 0)
            this_week_count = deliveries_this_week_map.get(driver.id, 0)
            prev_week_count = deliveries_prev_week_map.get(driver.id, 0)
            total_deliveries_all += all_deliveries_count
            total_deliveries_prev_all += prev_week_count
            if prev_week_count > 0:
                growth = ((this_week_count - prev_week_count) / prev_week_count) * 100
            elif prev_week_count == 0 and this_week_count > 0:
                growth = 100
            else:
                growth = 0

            driver_summary_list.append({
                'driver_name': driver_names[driver.id],
                'email': driver.email,
                'orders_delivered': all_deliveries_count,
                'weekly_growth_pct': round(growth, 1),
            })

        # Sort driver summary by orders_delivered descending
        driver_summary_list.sort(key=lambda x: x['orders_delivered'], reverse=True)

        # Build daily driver deliveries (last 7 days)
        days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Single aggregated query: counts per driver per day
        deliveries_agg = (
            Delivery.objects.filter(
                driver_id__in=driver_ids,
                actual_delivery_completed_time__date__range=[start_date, end_date],
                status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS,
            )
            .annotate(day=TruncDate('actual_delivery_completed_time'))
            .values('driver_id', 'day')
            .annotate(count=Count('id'))
        )
        
        print(deliveries_agg, 'deliveries_agg--------------->')

        # Build a nested dict: {day: {driver_name: count, ...}, ...}
        daily_deliveries_map = defaultdict(lambda: defaultdict(int))
        for item in deliveries_agg:
            day = item['day']
            driver_name = driver_names[item['driver_id']]
            daily_deliveries_map[day][driver_name] = item['count']

        # Build the daily_deliveries_list with all days and all drivers included
        daily_deliveries_list = []
        for day in days:
            day_label = f"{day.strftime('%Y-%m-%d')} ({day.strftime('%a')})"
            deliveries_for_day = {}
            for driver in drivers:
                driver_name = driver_names[driver.id]
                deliveries_for_day[driver_name] = daily_deliveries_map[day].get(driver_name, 0)
            daily_deliveries_list.append({'day': day_label, 'deliveries': deliveries_for_day})

        # Filter deliveries in the date range
        deliveries = Delivery.objects.filter(created_date__date__range=[start_date, end_date])
        
        # Total number of deliveries
        total_deliveries = deliveries.count()

        # Total number of completed deliveries (DELIVERY_SUCCESS)
        completed_deliveries = deliveries.filter(status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS).count()
        print(completed_deliveries, 'completed_deliveries--------------->')
        completed_deliveries_prev = Delivery.objects.filter(
            actual_delivery_completed_time__date__range=[prev_week_start, prev_week_end],
            status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS
        ).count()

        if total_deliveries > 0:
            average_fulfillment_rate = (completed_deliveries / total_deliveries) * 100
        else:
            average_fulfillment_rate = 0.0
        # fulfillment rate change % (compared to previous week)  
        fulfillment_rate_change_pct = 0.0
        # Calculate previous period fulfillment rate first
        if total_deliveries_prev_all > 0:
            prev_fulfillment_rate = (completed_deliveries_prev / total_deliveries_prev_all) * 100
        else:
            prev_fulfillment_rate = 0.0

        fulfillment_rate_change_pct = 0.0
        if prev_fulfillment_rate > 0:
            fulfillment_rate_change_pct = ((average_fulfillment_rate - prev_fulfillment_rate) / prev_fulfillment_rate) * 100
        # Calculate overall driver delivery count change %
        driver_delivery_count_change_pct = 0
        if total_deliveries_prev_all > 0:
            driver_delivery_count_change_pct = ((total_deliveries_all - total_deliveries_prev_all) / total_deliveries_prev_all) * 100
            
            
        # driver days since joined
        driver_days_since_joined = {}
        for driver in drivers:
            if driver.date_joined:
                days_since_joined = (now().date() - driver.date_joined.date()).days
                driver_days_since_joined[driver.id] = days_since_joined
            else:
                driver_days_since_joined[driver.id] = 0
                
        # Earnings and delivery count per driver
        driver_earnings_data = (
            Delivery.objects.filter(
                driver_id__in=driver_ids,
                status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS
            )
            .values('driver_id')
            .annotate(
                total_earnings=Sum('driver_earning'),
                total_deliveries=Count('id')
            )
        )
        driver_earning_map = {item['driver_id']: item['total_earnings'] or 0 for item in driver_earnings_data}

        
        driver_avg_cost_map = {}
        for item in driver_earnings_data:
            driver_id = item['driver_id']
            earnings = item['total_earnings'] or 0
            deliveries = item['total_deliveries'] or 0
            avg = earnings / deliveries if deliveries > 0 else 0
            driver_avg_cost_map[driver_id] = avg
            
        # driver specific delivery fulfillment rate
        driver_fulfillment_rate_map = {}
        for driver in drivers:
            driver_deliveries = Delivery.objects.filter(
                driver=driver,
                created_date__date__range=[start_date, end_date],
            )
            total_driver_deliveries = driver_deliveries.count()
            completed_driver_deliveries = driver_deliveries.filter(status=Delivery.STATUS_TYPE.DELIVERY_SUCCESS).count()
            if total_driver_deliveries > 0:
                fulfillment_rate = (completed_driver_deliveries / total_driver_deliveries) * 100
            else:
                fulfillment_rate = 0.0
            driver_fulfillment_rate_map[driver.id] = fulfillment_rate
        
        # specific driver on time delivery rate 
        driver_on_time_delivery_map = {}
        for driver in drivers:
            driver_deliveries = Delivery.objects.filter(
                driver=driver,
                actual_delivery_completed_time__date__range=[start_date, end_date],
            )
            total_driver_deliveries = driver_deliveries.count()
            on_time_deliveries = driver_deliveries.filter(
                actual_delivery_completed_time__lte=F('drop_off_last_time')
            ).count()
            if total_driver_deliveries > 0:
                on_time_rate = (on_time_deliveries / total_driver_deliveries) * 100
            else:
                on_time_rate = 0.0
            driver_on_time_delivery_map[driver.id] = on_time_rate
            
        # avg earning per month
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        driver_avg_earning_map = {}
        for driver_id, total_earning in driver_earning_map.items():
          avg_earning = total_earning / months if months > 0 else 0
          driver_avg_earning_map[driver_id] = avg_earning

        # total earnings for specific driver

        # Build driver details list
        driver_details_list = []
        for driver in drivers:
            driver_details_list.append({
                'driver_id': f"{driver.id}",
                'driver_name': " ".join(filter(None, [driver.first_name, driver.last_name])),
                'phone_number': driver.phone or '',
                'email': driver.email or '',
                'status': 'Active' if driver.is_active else 'Offline',
                'days_since_joined': driver_days_since_joined[driver.id],
                'avg_cost_per_delivery': round(driver_avg_cost_map.get(driver.id, 0), 2),
                'fulfillment_rate': round(driver_fulfillment_rate_map.get(driver.id, 0), 2),
                'on_time_delivery_rate': round(driver_on_time_delivery_map.get(driver.id, 0), 2),
                'total_earnings': round(driver_earning_map.get(driver.id, 0), 2),
                'avg_earning_per_month': round(driver_avg_earning_map.get(driver.id, 0), 2),
            })
            
        

        # Compose response
        response_data = {
            'greeting': greeting,
            'admin_name': admin_name,
            'average_fulfillment_rate': round(average_fulfillment_rate, 2),
            'fulfillment_rate_change_pct': round(fulfillment_rate_change_pct, 1),
            'driver_delivery_count': total_deliveries_all,
            'driver_delivery_count_change_pct': round(driver_delivery_count_change_pct, 1),
            'daily_driver_deliveries': daily_deliveries_list,
            'driver_summary': driver_summary_list,
            'driver_details': driver_details_list,
        }

        serializer = DashboardSerializer(instance=response_data)
        return Response(serializer.data)
      
      
class BaseDeliveryIssueCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Returns a list of delivery issues.
        """
        issues = DeliveryIssue.objects.all()
        serializer = DeliveryIssueSerializer(issues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = DeliveryIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
      
    def patch(self, request, pk):
        """
        Updates a delivery issue.
        """
        issue = get_object_or_404(DeliveryIssue, pk=pk)
        serializer = DeliveryIssueSerializer(issue, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    def delete(self, request, pk):
        """
        Deletes a delivery issue.
        """
        issue = get_object_or_404(DeliveryIssue, pk=pk)
        issue.delete()
        return Response({"message": "Delivery issue deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    