import requests
import json
from . import content
import os
headers = {'Content-Type': 'application/json', 'authkey': '250788ACjjQklCDp7f5c0a186c'}


uri = 'http://api.msg91.com/api/v2/sendsms'

body = {
  "sender": "Ashram",
  "route": "4",
  "country": "91",
  "sms": [
    {
      "message": "",
      "to": []
    }
  ]
}


def sendsms(mobile, code, *args):
    if args[0] == 0:
        message = content.register_phone['subject']
        body['sms'][0]['message'] = str(code) + message
        body['sms'][0]['to'].append(str(mobile))
    elif args[0] == 1:
        body['sms'][0]['message'] = content.create_booking_mobile['subject']
        body['sms'][0]['to'].append(str(mobile))
    elif args[0] == 2:
        body['sms'][0]['message'] = content.update_booking_mobile['subject']
        body['sms'][0]['to'].append(str(mobile))

    a = requests.post(uri, data=json.dumps(body), headers=headers)
    # print(a.content)


if __name__ == '__main__':
    # Testing
    # print(os.environ.get('authkey'))
    sendsms(9182957004, 1212)
