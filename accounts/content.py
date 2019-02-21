
from AshramAccomodate.settings import BASE_URL
# This file contain all the mail subjects and messages

# Four kinds of mails (presently)
# 1. User registration -- 0
# 2. User email change -- 1
# 3. User Forgot password -- 2
# 4. User Registration success -- 3/Failure --4


registration = {}
registration['uri'] = BASE_URL + 'accounts/mail_verify/'
registration['subject'] = 'Mail Verification at OnlinePortal'
registration['pre_message'] = '<b>Thanks</b> for registration. Please <a href='
registration['post_message'] = '>click here</a> to confirm the registration.'


forgot_password = {}
forgot_password['uri'] = BASE_URL + 'accounts/forgot_password_update/'
forgot_password['subject'] = 'Forgot password operation'
forgot_password['pre_message'] = 'There is a password request operation from our account <a href='
forgot_password['post_message'] = '>click here</a> to change. If you haven\'t made any request, ignore the mail'


email_change = {}
email_change['uri'] = BASE_URL + 'accounts/email_verify/'
email_change['subject'] = 'Email change Operation'
email_change['pre_message'] = 'There is a email change operation from our account <a href='
email_change['post_message'] = '>click here</a> to change. If you haven\'t made any request, ignore the mail'



register_phone = {}
register_phone['subject'] = ' is your One Time Password to proceed for Room booking. It is valid for 10 mins, ' \
                            'Don\'t share this OTP with anyone else'
