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

class Playlist(object):
    """Playlist Class

    A playlist class takes in a JSON formatted item, and parses it to create a 
    usable data object.

    Attributes
    ----------
    description : str
        Description of the playlist
    name : str
        Name of the playlist
    owner : str
        Display name of the owner of the playlist
    tracks : list
        List of Track objects containing information about the songs on the
        playlist
    tracks_size : int
        Number of tracks in the playlist
    tracks_uri : str
        URI to query for track information
    uri : str
        URI to query for information directly
    """
    def __init__(self, data: dict):
        """Parse the data object containing playlist attributes

        Parameters
        ----------

        data : dict
            Dictionary containing attributes of a playlist
        """
        # Check that the JSON we are about to parse is of type "playlist"
        if 'type' not in data.keys():
            if data['type'] is not 'playlist':
                raise Exception("data is not of type \"playlist\"")

        # Parse out the relevant attributes
        if 'description' in data.keys():
            self.description = data['description']
        if 'name' in data.keys():
            self.name = data['name']
        if 'owner' in data.keys():
            self.owner = data['owner']
        if 'tracks' in data.keys():
            self.tracks_size = data['tracks']['total']
            self.tracks_uri = data['tracks']['href']
        if 'href' in data.keys():
            self.uri = data['href']

    def __len__(self):
        return self.tracks_size

    def __repr__(self):
        return f"[Playlist: {self.name} ({self.tracks_size} tracks)]"

    def get_tracks(self, oauth: OAuth2Session):
        """For this playlist, retrieve all track information

        Paramters
        ---------
        oauth : object
            OAuth2 session object to use for querying for the tracks for this
            playlist.

        Returns
        ------
        bool
            A boolean value. `True` if all tracks have been successfully
            retrieved; `False` otherwise.
        """
        ret = False

        if oauth is not None:
            response = oauth.get(self.tracks_uri)

            # TODO: Check that the track number returned in the response matches
            # the number expected in self.track_size.

            with open("trackdata.json", "w") as f:
                import json
                json.dump(response.json(), f, indent=True)
        
        return True


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


def spotify_get_playlists(oauth: OAuth2Session, user: str) -> list:
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
    playlists = list()
    num_playlists = 0

    response = oauth.get(SPOTIFY_BASE_URL + f'/users/{user}/playlists')

    print(f"[+] JSON: {response.json()}")

    #import json
    #with open("testdata.json", "w") as f:
    #    json.dump(playlists.json(), f, indent=True)

    if response.status_code == 200:
        # Extract the JSON object from the response.
        data = response.json()
        
        # Check the number of playlists in the response against the "total" number
        # expected.       
        expected_size = data['total']
        total_size = len(data['items'])

        if expected_size == total_size:
            for item in data['items']:
                print(f"Item: {item}")
                playlists.append(Playlist(item))
            
            print(f"[+] Found {len(playlists)} playlists")

        else:
            print(f"[!] Expected {expected_size} playlists, data contained {total_size}")
        
    else:
        print(f"[!] Playlist request failed with HTTP status code {response.status_code}")

    return playlists


def spotify_get_tracks(oauth: OAuth2Session, playlists: list):
    """A function to retrive the songs for a Spotify playlist.

    Given the Spotify object and list of playlists, retrieve all songs
    and their information.

    Parameters
    ----------
    oauth : object
        Oauth2 session object to make the requests for each playlist.
    playlists : list
        List of `Playlists` for the given Spotify object to request their song
        information.
    """
    for playlist in tqdm(playlists):
        playlist.get_tracks(oauth)


def get_arguments():
    parser = argparse.ArgumentParser(DESCRIPTION)
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
    playlists = spotify_get_playlists(session, args.user)

    # 3. Retrieve all songs for each playlist found.
    if len(playlists) > 0:
        spotify_get_tracks(session, playlists)

    # 4. For now, print the results as a dictionary/JSON object.


# Ensures that if this is imported as a module the main() function is not
# called. Only called if run as a script.
if __name__ == '__main__':
    main()