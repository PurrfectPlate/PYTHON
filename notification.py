from firebase_admin import firestore

class NotificationSender:
    def __init__(self, db):
        self.db = db
        self.collection_name = "notifications"

    def send_notification(self, message, device_name):
        notification_data = {
            "Messages": message,
            "hasSeen": False,
            "deviceName": device_name,
            "createdAt": firestore.SERVER_TIMESTAMP
        }

        notifications_ref = self.db.collection(self.collection_name)
        new_notification_ref = notifications_ref.add(notification_data)
        return new_notification_ref[1].id

    def fed_a_pet(self, pet_name, cups_ate, device_name, successful=True):
        if successful:
            message = f"Pet {pet_name} successfully ate {cups_ate} cup"
        else:
            message = f"Pet {pet_name} did not eat successfully"

        return self.send_notification(message, device_name)
    
    def goal_weight_achieved(self, pet_name, goalWeight, device_name, successful=True):
        if successful:
            message = f"Pet {pet_name} successfully achieved {goalWeight}kg weight!"
        else:
            message = f"Pet {pet_name} did not achieve goal weight on specified time."

        return self.send_notification(message, device_name)