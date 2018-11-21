""" Omar Shafie (OSMIUM), June 2018.

 This is a simple project that uses Youtube API v3.

 It manages my personal watch list on Youtube.
 It sorts videos by channels in round robin order.
"""
import os

import flask

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from functions import list_playlist_items, sort_by_channels, ordered_list, update_all

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

APP = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works, but if you
# use this code in your application please replace this with a truly secret
# key. See http://flask.pocoo.org/docs/0.12/quickstart/#sessions.
APP.secret_key = 'REPLACE ME - this value is here as a placeholder.'

PLAYLIST_ID = "PLm2PC68xR2108gCuX8pzAn95PsEgVAF52"

# This is called on http://localhost:8090/ after the server runs => python file.py
@APP.route('/')
def index():
    """ This function is called when index page is refreshed. """
    # authorize with youtube
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load the credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    client = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # PART I: GET ALL ITEMS IN PLAYLIST
    print"PART I"
    items = list_playlist_items(client, PLAYLIST_ID)

    # PART II.1: SORT VIDEOS BY PRODUCING CHANNEL
    print"PART II"
    dic_channels = sort_by_channels(client, items)

    # PART II.2: COMPUTE NEW POSITION IN PLAYLIST
    videos = ordered_list(dic_channels)

    # PART III: UPDATE PLAYLIST WITH NEW POSITIONS
    print"PART III"
    update_all(client, videos, PLAYLIST_ID)

    return ""

@APP.route('/authorize')
def authorize():
    """ Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow
    steps. """
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        # This parameter enables offline access which gives your application
        # both an access and refresh token.
        access_type='offline',
        # This parameter enables incremental auth.
        include_granted_scopes='true')

    # Store the state in the session so that the callback can verify that
    # the authorization server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@APP.route('/oauth2callback')
def oauth2callback():
    """ Specify the state when creating the flow in the callback so that it can
    # verify the authorization server response. """
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    # Store user's access and refresh tokens in your data store if
    # incorporating this code into your real app.
    credentials = flow.credentials
    flask.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return flask.redirect(flask.url_for('index'))

if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    APP.run('localhost', 8090, debug=True)
    