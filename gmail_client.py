"""
1. Follow the step 1 here:
https://developers.google.com/gmail/api/quickstart/python#step_1_turn_on_the_api_name
and store the file client_secret.json in this folder.

2. Install the requirements:
(venv)$ pip install -r

3. Run this script:
(venv)$ python gmail_client.py

Note1: on the first run a browser window will be open to prompt for user's
authorization. This authorization is then stored in the file system at:
~/.credentials/gmail_client_credentials.json

Note2: API docs for messages:
https://developers.google.com/gmail/api/v1/reference/users/messages
"""
from __future__ import print_function
import base64
import httplib2
import os
import traceback

from apiclient import discovery, errors
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GmailClient(object):
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/gmail-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Gmail API Python Client'

    def __init__(self):
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'gmail_client_credentials.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE,
                                                  self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def search_message(self, subject=''):
        try:
            response = self.service.users().messages().list(
                userId='me', q='subject:"{}"'.format(subject)).execute()
        except errors.HttpError:
            traceback.print_exc()

        if 'messages' not in response:
            print('No messages list in response!')
            return None

        try:
            message = response['messages'][0]
        except IndexError as exc:
            print('The messages list is empty!')
            traceback.print_exc()

        return message.get('id', None)

    def get_message(self, message_id, is_html_mime=False):
        mime = 'text/plain'
        if is_html_mime:
            mime = 'text/html'

        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id).execute()
        except errors.HttpError:
            traceback.print_exc()

        body = None
        try:
            if 'multipart' in message['payload']['mimeType']:
                parts = message['payload']['parts']
            else:
                parts = [message['payload']]

            for part in parts:
                if part['mimeType'].lower() == mime:
                    body = part['body']['data'].encode('ASCII')
                    body = base64.urlsafe_b64decode(body)
        except TypeError:
            print('The body is probably not base64 encoded!')
            traceback.print_exc()
        except IndexError:
            print('The message dictionary is not properly built!')
            traceback.print_exc()

        return body


if __name__ == '__main__':
    client = GmailClient()
    subject = 'todo scalata stelvio'
    #subject = 'Je Tele2 factuur - Thuisabonnement'
    msg_id = client.search_message(subject)

    if not msg_id:
        print('No message found!')

    body = client.get_message(msg_id, is_html_mime=True)
    print('Body: {}'.format(body))
