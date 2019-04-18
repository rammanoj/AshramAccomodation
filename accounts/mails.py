from __future__ import print_function
from googleapiclient import discovery, errors
from httplib2 import Http
from oauth2client import file, client, tools
from AshramAccomodate.settings import STATIC_ROOT
from email.mime.text import MIMEText
from . import content
import base64
from AshramAccomodate import settings

SEND_MAIL = 'rammanojpotla1608@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/gmail.compose', 'https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.send']


def makehtml(**kwargs):
    print(kwargs)
    content = '<table style="width:100%">'
    for i in kwargs:
        if i == 'mail_type':
            continue

        value = kwargs[i]
        if i is 'proof':
            value = settings.BASE_URL + "media/" + kwargs[i].name
        content += '<tr><th>' + i + '</th><td>' + value + '</td></tr>'

    content += '</table>'
    return content


def send_mail(service, to_mail, *args, **kwargs):
    message = {}
    if kwargs['mail_type'] == 0:
        # user registration
        contents = content.registration['pre_message'] + content.registration['uri'] + kwargs['id'] + \
                   content.registration['post_message']
        message = MIMEText(contents, 'html')
        message['subject'] = content.registration['subject']
    elif kwargs['mail_type'] == 1:
        # Email change operation
        contents = content.email_change['pre_message'] + content.email_change['uri'] + kwargs['id'] + \
                   content.email_change['post_message']
        message = MIMEText(contents, 'html')
        message['subject'] = content.email_change['subject']
    elif kwargs['mail_type'] == 2:
        # user forgot password
        contents = content.forgot_password['pre_message'] + content.forgot_password['uri'] + \
                  kwargs['id'] + content.forgot_password['post_message']
        message = MIMEText(contents, 'html')
        message['subject'] = content.forgot_password['subject']

    elif kwargs['mail_type'] == 3:
        # user Booked a Room
        contents = content.create_booking['message'] + makehtml(**kwargs)
        message = MIMEText(contents, 'html')
        message['subject'] = content.create_booking['subject']
    elif kwargs['mail_type'] == 4:

        # user updated the booking
        contents = content.update_booking['message'] + makehtml(**kwargs)
        message = MIMEText(contents, 'html')
        message['subject'] = content.update_booking['subject']

    elif kwargs['mail_type'] == 5:
        # user Deleted Booking
        contents = content.delete_booking['message'] + kwargs['reference']
        message = MIMEText(contents, 'html')
        message['subject'] = content.delete_booking['subject']

    message['to'] = to_mail
    message['from'] = SEND_MAIL

    msg = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    try:
        service.users().messages().send(userId='me', body=msg).execute()
        print("mail sent successfully")
        return 1
    except errors.HttpError as error:
        print("error in sending mail")
        print(error)
        return 0


def main(to_mail, *args, **kwargs):
    store = file.Storage(STATIC_ROOT + '/accounts/json/token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets((STATIC_ROOT + '/accounts/json/credentials.json'), SCOPES)
        creds = tools.run_flow(flow, store)
    service =discovery.build('gmail', 'v1', http=creds.authorize(Http()))

    return send_mail(service, to_mail, *args, **kwargs)


# if __name__ == '__main__':
#     kwargs = {'meail_type': 0, 'id': 1}
#     main(to_mail='rammanojpotla1608@gmail.com', **kwargs)
