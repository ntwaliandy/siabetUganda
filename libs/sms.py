from __future__ import print_function

import africastalking


class SMS:
    def __init__(self):
        # Set your app credentials
        self.username = 'sandbox'
        self.api_key = '3aed45020b13e634d56f624d90db883dae4edef029498f82f532db6546dbde33'
        # Initialize the SDK
        africastalking.initialize(self.username, self.api_key)

        # Get the SMS service
        self.sms = africastalking.SMS

    def send(self, message, receiver):
        # Set the numbers you want to send to in international format
        recipients = [receiver]

        # Set your shortCode or senderId
        sender = 61128
        try:
            # Thats it, hit send and we'll take care of the rest.
            response = self.sms.send(message, recipients, sender)
            print(response)
        except Exception as e:
            print('Encountered an error while sending: %s' % str(e))


sms = SMS()
if __name__ == '__main__':
    sms().send()
