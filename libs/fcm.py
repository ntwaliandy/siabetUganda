from pyfcm import FCMNotification
from config import fcm_api_key


class FCM:
    def __init__(self):
        # Set your app credentials
        self.api_key = fcm_api_key
        self.push_service = FCMNotification(api_key=self.api_key)

    def send(self, registration_id, content, is_topic=None, topic_name=None):
        if is_topic is not None and topic_name is not None:
            result = self.push_service.notify_topic_subscribers(topic_name=topic_name, data_message=content)
            print(result)
        else:
            result = self.push_service.notify_single_device(registration_id=registration_id, data_message=content)
        return result

    def manage_subscription(self, tokens, channel, operation):
        if operation == "subscribe":
            return self.push_service.subscribe_registration_ids_to_topic(tokens, channel)
        elif operation == "unsubscribe":
            return self.push_service.unsubscribe_registration_ids_from_topic(tokens, channel)
        else:
            return False


fcm = FCM()
if __name__ == '__main__':
    fcm().send()
