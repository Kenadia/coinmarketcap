import config
import twilio.rest

class Client(object):

  def __init__(self):
    self.number = config.phone_number
    self.client = twilio.rest.Client(config.account_sid, config.auth_token)

  def send(self, to, body):
    self.client.messages.create(body=body, to=to, from_=self.number)
