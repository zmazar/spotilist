"""Spotilist

For a given user this script will login to their Spotify account, and retrieve
all playlists associated with that account. Then it will retrieve all song 
information for each playlist. This data will be written to a CSV formatted
file to be imported into a Spreadsheet.
"""

# Standard imports
import argparse

# Dependency imports
from tqdm import tqdm
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth

# Help menu strings
DESCRIPTION='''Dump the playlists for a given Spotify user.'''
HELP_P='''Password for the Spotify account'''
HELP_U='''Username for the Spotify account'''

# OAuth Client Key for our "app"
API_CLIENT_ID = "b642673a942947c4b2b5c193bf4a0df4"
API_CLIENT_SECRET = "2ec47cef47a4434b9921447f075f1b36"

# Spotify API URLs
SPOTIFY_BASE_URL='https://api.spotify.com/v1'
SPOTIFY_TOKEN_URL='https://accounts.spotify.com/api/token'


def spotify_login():
    """A function to log a user into Spotify.

    Given a user's credentials it will create a connection to Spotify using the
    API for this script.

    Parameters
    ----------
    user : str
        Username for logging into Spotify.
    password : str
        Passoword for the given user.
    
    Returns
    -------
    object
        OAuth2 session object
    object
        Spotilist authorization token
    """
    auth = HTTPBasicAuth(API_CLIENT_ID, API_CLIENT_SECRET)
    client = BackendApplicationClient(client_id=API_CLIENT_ID)
    spotify = OAuth2Session(client=client)
    token = spotify.fetch_token(                              \
        token_url=SPOTIFY_TOKEN_URL,                        \
        auth=auth,                                          \
        )
    
    return spotify, token


def spotify_get_playlists(oauth: object, token: object, user: str) -> list:
    """A function to get all playlists for a user.
    
    Using the given `spotify` object, retrieve all playlists associated with
    the account.

    Parameters
    ----------
    spotify : object
        The spotify object associated with the account to retrieve playlists.
    
    Returns
    -------
    list
        List of spotify playlists for the given Spotify account.
    """
    playlists = None

    playlists = oauth.get(SPOTIFY_BASE_URL + f'/users/{user}/playlists')

    print(f"[+] playlists type: {type(playlists)}")
    print(f"[+] JSON: {playlists.json()}")

    return playlists


def spotify_get_songs(spotify: object, playlists: list):
    """A function to retrive the songs for a Spotify playlist.

    Given the Spotify object and list of playlists, retrieve all songs
    and their information.

    Parameters
    ----------
    spotify : object
        Spotify object needed to make the requests for each playlist.
    playlists : list
        List of playlists for the given Spotify object to request their song
        information.
    """
    pass


def get_arguments():
    parser = argparse.ArgumentParser(DESCRIPTION)
    parser.add_argument('-p', '--password', help=HELP_P)
    parser.add_argument('-u', '--user', help=HELP_U)
    
    return parser.parse_args()

def main():
    args = get_arguments()
    playlists = None
    session = None
    spotify_token = None

    print("[+] Attempting login for {user}")

    # 1. Login to spotify using the given credentials.
    session, spotify_token = spotify_login()

    if session is None or spotify_token is None:
        print(f"[!] Error acquiring Spotilist authorization token.")
        return

    print(f"[+] Session: {session}")
    print(f"[+] Token: {spotify_token}")
    
    # 2. Get all playlists that can be retrieved for the account.
    playlists = spotify_get_playlists(session, spotify_token, args.user)

    print(f"[+] Playlists: {playlists}")

    ## 3. Retrieve all songs for each playlist found.
    #if len(playlists) > 0:
    #    num_retrieved = spotify_get_songs(spotify, playlists)
    #    print("[+] Retrieved {num_retrieved} playlists")

    # 4. For now, print the results as a dictionary/JSON object.


# Ensures that if this is imported as a module the main() function is not
# called. Only called if run as a script.
if __name__ == '__main__':
    main()