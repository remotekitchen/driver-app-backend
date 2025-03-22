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
                title=data["campaign_title"],
                body=data["campaign_message"],
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
    Generate a dynamic title and message body for a given event type tailored to a fast-paced food delivery raider app.
    """

    print("🔥 Generating dynamic message for:", order, event_type)

    if event_type == "created":
        title = f"🎯 Mission Started: Order #{order.id} Placed!"
        body = f"A new order just dropped at {restaurant_name}. Gear up — it’s go time! 💥🍽️"

    elif event_type == "waiting_for_driver":
        title = f"🕵️ Searching for a Raider for Order #{order.id}"
        body = f"Looking for the fastest raider to take on this mission from {restaurant_name}. Stand by! 🔍"

    elif event_type == "driver_assign":
        title = f"🎮 Raider Assigned to Order #{order.id}!"
        body = f"A top raider is en route to {restaurant_name} for pickup. Lock and load! ⚡🏍️"

    elif event_type == "order_picked_up":
        title = f"📦 Package Secured: Order #{order.id} Picked Up!"
        body = f"The raider has grabbed the goods from {restaurant_name}. The run begins! 🚀"

    elif event_type == "on_the_way":
        title = f"🛣️ Order #{order.id} In Transit!"
        body = f"The raider is blazing through the streets with your meal. ETA: soon! 🔥"

    elif event_type == "arrived":
        title = f"📍 Drop Point Reached for Order #{order.id}!"
        body = f"The raider is at your doorstep. Time to collect your feast! 🍱⚔️"

    elif event_type == "delivery_success":
        title = f"✅ Mission Complete: Order #{order.id} Delivered!"
        body = f"Another successful raid! Your meal has arrived — dig in, hero. 🥇🍕"

    elif event_type == "delivery_failed":
        title = f"❌ Mission Failed: Order #{order.id}"
        body = f"The raid couldn’t be completed. Reach out to support to regroup. 🛠️"

    elif event_type == "driver_rejected":
        title = f"🚫 Raider Declined Order #{order.id}"
        body = f"A raider couldn’t take the mission. Searching for the next available warrior. ♻️"

    elif event_type == "canceled":
        title = f"🗑️ Order #{order.id} Canceled"
        body = f"This mission has been called off. For more info, reach out to HQ. 🧭"

    else:
        title = f"ℹ️ Update on Order #{order.id}"
        body = f"Status update received. Check your dashboard for the latest intel. 🛰️"

    return title, body
