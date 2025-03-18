from firebase_admin import messaging, credentials
from apps.firebase.models import TokenFCM





def send_push_notification(tokens, data):

    print(f"Sending to {len(tokens)} devices")
    
    results = {
        "successful": 0,
        "failed": 0,
        "failures": [],
        "invalid_tokens": []  
    }
    
    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(
                title="hello me notification",
                body="me notification body",
                image="imagurl.png",  
            ),
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    icon="notification_icon",  # Icon resource name in your Android app
                    color="#FF0000",  # Accent color for the notification
                    image="https://www.example.com/notification-image.jpg",  # Android large image
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=1,  # iOS badge count
                        mutable_content=True,  # Required for iOS to download and display images
                        sound="default"
                    )
                ),
                fcm_options=messaging.APNSFCMOptions(
                    image="https://www.example.com/notification-image.jpg"  # iOS image URL
                )
            ),
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    icon="https://www.example.com/icon.png",  # Web notification icon
                    badge="https://www.example.com/badge.png",  # Web notification badge
                    image="https://www.example.com/image.jpg"  # Web notification image
                )
            ),
            data={
                "click_action": "https://www.hungry-tiger.com/",
                # "image_url": str(campaign_image),  # Also including in data for custom handling
                # "badge_count": "1",
                # "campaign_category": str(campaign_category),
                # "campaign_is_active": str(campaign_is_active),
                # "restaurant_name": str(restaurant_name),
            },
            token=token
        )

        try:
            response = messaging.send(message)
            print(f"Notification sent successfully to {token[:10]}...: {response}")
            results["successful"] += 1
        except Exception as e:
            error_message = f"Error sending to {token[:10]}...: {e}"
            print(error_message)
            results["failed"] += 1
            results["failures"].append({"token": token, "error": str(e)})
            
            error_str = str(e).lower()
            if any(reason in error_str for reason in [
                "invalid registration", 
                "not registered", 
                "invalid token", 
                "unregistered", 
                "expired"
            ]):
                results["invalid_tokens"].append(token)
                print(f"Token marked for removal: {token[:10]}...")
    print("invalid token", results["failures"])
    # Remove all failed tokens from TokenFCM
    if results["invalid_tokens"]:
        remove_invalid_tokens_from_database(results["invalid_tokens"])
        print(f"Removed {len(results['invalid_tokens'])} invalid tokens from TokenFCM database")
    elif results["failures"]:
        # If we didn't catch any as invalid but there were failures, remove those tokens too
        failed_tokens = [failure["token"] for failure in results["failures"]]
        remove_invalid_tokens_from_database(failed_tokens)
        print(f"Removed {len(failed_tokens)} failed tokens from TokenFCM database")
    return results


def remove_invalid_tokens_from_database(invalid_tokens):
    """
    Remove invalid tokens from the TokenFCM database using Django ORM
    """
    
    removed_count = 0
    for token_value in invalid_tokens:
        try:
            # Find the TokenFCM object by token value
            token_objects = TokenFCM.objects.filter(token=token_value)
            
            # Delete all matching objects
            deleted_count = token_objects.delete()[0]
            removed_count += deleted_count
            print(f"Removed {deleted_count} records for token {token_value[:10]}...")
        except Exception as e:
            print(f"Error removing token {token_value[:10]}...: {e}")
    
    print(f"Successfully removed {removed_count} token records from database")



    """
    Remove invalid tokens from the TokenFCM database using Django ORM
    """
    print("invalid_tokens", invalid_tokens)
    removed_count = 0
    for token_value in invalid_tokens:
        print(token_value, "token value")
        try:
            # Find the TokenFCM object by token value
            # Assuming you have a field named 'token' that stores the token value
            token_objects = TokenFCM.objects.filter(token=token_value)
            
            # Delete all matching objects
            deleted_count = token_objects.delete()[0]
            removed_count += deleted_count
            print(f"Removed {deleted_count} records for token {token_value[:10]}...")
        except Exception as e:
            print(f"Error removing token {token_value[:10]}...: {e}")
    
    print(f"Successfully removed {removed_count} token records from database")








def get_dynamic_message(order, event_type, restaurant_name):
    """
    Generate a dynamic title and message body for a given event type.
    """
    
    print("im get daynamic message", order, event_type)
    if event_type == "pending":
        title = f"#{order.id} Order Placed! 🎉"
        body = f"We’ve got your order! Just waiting for {restaurant_name} to give the thumbs up. 🤞"
    
    elif event_type == "order_accepted":
        title = f"#{order.id} ✅ Order Accepted – Chef’s on It!"
        body = f"{restaurant_name} has accepted your order. The kitchen is heating up! 🔥"
    
    elif event_type == "order_scheduled_accepted":
        title = f"Order #{order.id} Scheduled"
        body = f"Your order has been scheduled and accepted. Your delivery is on the way!"
    
    elif event_type == "order_not_ready_for_pickup":
        title = f"Order #{order.id} Not Ready"
        body = f"Your order is not ready for pickup yet. We'll update you when it's ready."
    
    elif event_type == "order_waiting_for_driver":
        title = f"Order #{order.id} Waiting for Driver"
        body = f"Your order is waiting for a driver to pick it up."
    
    elif event_type == "order_driver_assigned":
        title = f"Driver Assigned to Order #{order.id}"
        body = f"A driver has been assigned for your order. They'll be with you soon!"
    
    elif event_type == "order_ready_for_pickup":
        title = f"Order #{order.id} Ready for Pickup"
        body = f"Your order is ready for pickup!"
    
    elif event_type == "order_rider_confirmed":
        title = f"Rider Confirmed for Order #{order.id}"
        body = f"Your rider has confirmed pickup for your order. They're on their way."
    
    elif event_type == "order_rider_confirmed_pickup_arrival":
        title = f"🚗 Driver On the Way!"
        body = f"The Restaurant has served dinner, and the rider is rushing to the merchant."
    
    elif event_type == "order_rider_on_the_way":
        title = f"Rider On the Way for Order #{order.id}"
        body = f"Your rider is on the way with your order. Stay tuned!"
    
    elif event_type == "order_rider_picked_up":
        title = f"Rider Picked Up Order #{order.id}"
        body = f"Your order has been picked up by the rider and is on its way to you."
    
    elif event_type == "order_rider_confirmed_dropoff_arrival":
        title = f"⏳ Almost There – Get Ready!"
        body = f"Your food is just minutes away! Grab your napkins and get ready. 😋"
    
    elif event_type == "order_completed":
        title = f"Delivered! 🍕🎉"
        body = f"Bon appétit! Your order has arrived. Time to dig in! 🍽️"
    
    elif event_type == "order_cancelled":
        title = f"Order Canceled 😢"
        body = f"Your order has been canceled. Need help? Contact support or place a new order."
    
    elif event_type == "order_rejected":
        title = f"Order #{order.id} Rejected"
        body = f"Your order has been rejected. Please try placing it again later."
    
    elif event_type == "order_missing":
        title = f"Order #{order.id} Missing"
        body = f"Your order is missing. We're looking into this and will update you soon."
    
    elif event_type == "order_na":
        title = f"Order #{order.id} Status Unavailable"
        body = f"Your order status is currently unavailable. Please check back later."

    else:
        title = "Order Notification"
        body = "No specific message available."

    return title, body
