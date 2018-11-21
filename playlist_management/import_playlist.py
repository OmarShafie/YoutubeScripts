""" Omar Shafie (OSMIUM), June 2018.

 This is a simple project that uses Youtube API v3.

 It imports any public playlist into my personal watch playlist.
"""

import os

import flask

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this APPlication, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"
PLAYLIST_ID = "PL8dPuuaLjXtNcAJRf3bE1IJU6nMfHj86W"
WATCHLIST_ID = "PLm2PC68xR2108gCuX8pzAn95PsEgVAF52"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

APP = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works, but if you
# use this code in your APPlication please replace this with a truly secret
# key. See http://flask.pocoo.org/docs/0.12/quickstart/#sessions.
APP.secret_key = 'REPLACE ME - this value is here as a placeholder.'


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


    req = client.playlistItems().list(
        part='contentDetails',
        maxResults=25,
        playlistId=PLAYLIST_ID
    )

    content = []

    while req:
        res = req.execute()
        content += res["items"]
        req = client.playlistItems().list_next(req, res)

    for i in content:
        properties = {
            'snippet.playlistId': WATCHLIST_ID,
            'snippet.resourceId.kind': 'youtube#video',
            'snippet.resourceId.videoId': i[u'contentDetails'][u'videoId']
        }
        playlist_items_insert(client, properties, part='snippet')

    return ""

def playlist_items_insert(client, properties, **kwargs):
    """ Copied from API """
    resource = build_resource(properties)

    # See full sample for function
    kwargs = remove_empty_kwargs(**kwargs)

    return client.playlistItems().insert(
        body=resource,
        **kwargs
    ).execute()

@APP.route('/authorize')
def authorize():
    """ Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow
        steps. """
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        # This parameter enables offline access which gives your APPlication
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
        verify the authorization server response."""
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
    # incorporating this code into your real APP.
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

# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
    """ Taken from API Doc """
    resource = {}
    for prop in properties:
        # Given a key like "snippet.title", split into "snippet" and "title", where
        # "snippet" will be an object and "title" will be a property in that object.
        prop_array = prop.split('.')
        ref = resource
        for parr in range(0, len(prop_array)):
            is_array = False
            key = prop_array[parr]

            # For properties that have array values, convert a name like
            # "snippet.tags[]" to snippet.tags, and set a flag to handle
            # the value as an array.
            if key[-2:] == '[]':
                key = key[0:len(key)-2:]
                is_array = True

            if parr == (len(prop_array) - 1):
                # Leave properties without values out of inserted resource.
                if properties[prop]:
                    if is_array:
                        ref[key] = properties[prop].split(',')
                    else:
                        ref[key] = properties[prop]
            elif key not in ref:
                # For example, the property is "snippet.title", but the resource does
                # not yet have a "snippet" object. Create the snippet object here.
                # Setting "ref = ref[key]" means that in the next time through the
                # "for pa in range ..." loop, we will be setting a property in the
                # resource's "snippet" object.
                ref[key] = {}
                ref = ref[key]
            else:
                # For example, the property is "snippet.description", and the resource
                # already has a "snippet" object.
                ref = ref[key]
    return resource

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
    """ Copied from API """
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if value:
                good_kwargs[key] = value
    return good_kwargs

def playlist_item_update_position(client, properties, **kwargs):
    """ Copied from API """
    resource = build_resource(properties)

    # See full sample for function
    kwargs = remove_empty_kwargs(**kwargs)

    return client.playlistItems().update(
        body=resource,
        **kwargs
    ).execute()

def video_by_id(client, **kwargs):
    """ Copied from API """
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.videos().list(
        **kwargs
    ).execute()

    if response:
        channel_id = response["items"][0]["snippet"]["channelId"]
    return channel_id

if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    APP.run('localhost', 8090, debug=True)
    