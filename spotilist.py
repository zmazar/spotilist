"""Spotilist

For a given user this script will login to their Spotify account, and retrieve
all playlists associated with that account. Then it will retrieve all song 
information for each playlist. This data will be written to a CSV formatted
file to be imported into a Spreadsheet.
"""

# Standard imports
import argparse
import csv

# Dependency imports
from tqdm import tqdm
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth

# Help menu strings
DESCRIPTION='''Dump the playlists for a given Spotify user.'''
HELP_O='''Output file name'''
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
            if data['type'] != 'playlist':
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
        
        # Initialize the track listing
        self.tracks = list()

    def __len__(self):
        return self.tracks_size

    def __repr__(self):
        return f"[Playlist: {self.name} ({self.tracks_size} tracks)]"

    def get_tracks(self, session: OAuth2Session):
        """For this playlist, retrieve all track information

        Paramters
        ---------
        session : object
            OAuth2 session object to use for querying for the tracks for this
            playlist.

        Returns
        ------
        bool
            A boolean value. `True` if all tracks have been successfully
            retrieved; `False` otherwise.
        """
        ret = False

        if session is not None:
            downloaded = self.__download_tracks(session)

            if downloaded is not None:
                for track in downloaded:
                    self.tracks.append(Track(track))
                ret = True
        else:
            print(f"[!] OAuth2Session object is `None`")


        return ret

    def write_csv(self, writer):
        writer.writerow([self.name]) 
        writer.writerow(["Track", "Album", "Artist", "Spotify URL"])

        for track in self.tracks:
            row = [track.name, track.album, track.artist, track.spotify_url]
            writer.writerow(row)

        writer.writerow(["-"] * 4)
    
    def print_tracks(self):
        for track in self.tracks:
            print(track)

    def __download_tracks(self, session: OAuth2Session) -> list:
        dlist = list()
        index = 0

        while index < self.tracks_size:
            query = {"limit" : 50, "offset" : index}
            response = session.get(self.tracks_uri, params=query)

            if response.status_code == 200:
                data = response.json()

                if 'items' in data.keys():
                    dlist += data['items']
                    index += len(data['items'])
            else:
                print(f"[!] Error downloading {self.name} tracks, stopping download")
                index = self.tracks_size + 1
        # End while-loop

        # Check that all tracks for the playlist have been downloaded.
        if len(dlist) != self.tracks_size:
            print(f"[!] Failed to retrieve all tracks in response")
            dlist = None

        return dlist

class Track(object):
    """A class for handling data related to tracks

    Attributes
    ----------
    album : str
        Album the track is on
    artist : str
        Name of the band
    name : str
        Name of the track
    spotify_url : str
        Spotify URL for the track
    track : dict
        Raw dictionary for the track
    track_number : int
        Track number on the album
    """
    def __init__(self, data):
        """Parse the data object containing playlist attributes

        Parameters
        ----------

        data : dict
            Dictionary containing attributes of a track
        """
        # Pretty much only care about `track` within the data provided.
        if 'track' in data.keys():
            self.track = data['track']
        else:
            raise Exception("Invalid track dictionary for initialization")

        # Check that the JSON we are about to parse is of type "track"
        if self.track['type'] != 'track':
            raise Exception("data is not of type \"track\"")
        if not data['track']:
            raise Exception("data is not of type \"track\"")


        if 'album' in self.track.keys():
            self.album = self.track['album']['name']
        if 'artists' in self.track.keys():
            if len(self.track['artists']) > 0:
                # If there are artists associated with this track we only
                # care about the first.
                artist = self.track['artists'][0]
                self.artist = artist['name']
                self.spotify_url = artist['external_urls']['spotify']

        self.name = self.track['name']
        self.track_number = self.track['track_number']
    
    def __repr__(self):
        return f"[Track: {self.name} by {self.artist} ({self.album})"


def spotify_login():
    """A function to log a user into Spotify.

    Given a user's credentials it will create a connection to Spotify using the
    API for this script.

    Parameters
    ----------
    user : str
        Username for logging into Spotify
    
    Returns
    -------
    OAuth2Session
        OAuth2 session object to make requests to the Spotify API
    """
    auth = HTTPBasicAuth(API_CLIENT_ID, API_CLIENT_SECRET)
    client = BackendApplicationClient(client_id=API_CLIENT_ID)

    # This establishes the main object that is used to make requests to the 
    # Spotify API.
    spotify = OAuth2Session(client=client)

    # While the token isn't necessary for making requests through the OAuth2
    # session, this call needs to happen in order to establish an authenticated
    # session.
    token = spotify.fetch_token(token_url=SPOTIFY_TOKEN_URL, auth=auth)
    
    return spotify


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

    if response.status_code == 200:
        # Extract the JSON object from the response.
        data = response.json()
        
        # Check the number of playlists in the response against the "total" number
        # expected.       
        expected_size = data['total']
        total_size = len(data['items'])

        if expected_size == total_size:
            for item in data['items']:
                playlists.append(Playlist(item))
            
            print(f"[+] Found {len(playlists)} playlists")
        else:
            print(f"[!] Expected {expected_size} playlists, data contained {total_size}")
    else:
        print(f"[!] Playlist request failed with HTTP status code {response.status_code}")

    return playlists


def get_arguments():
    parser = argparse.ArgumentParser(DESCRIPTION)
    parser.add_argument('-o', '--output', help=HELP_O)
    parser.add_argument('-u', '--user', help=HELP_U)
    
    return parser.parse_args()


def main():
    args = get_arguments()
    playlists = None
    session = None

    # 1. Login to spotify using the given credentials.
    session = spotify_login()

    if session is None:
        print(f"[!] Error acquiring Spotilist authorization token.")
        return

    print("[+] Spotilist session created to Spotify")

    # 2. Get all playlists that can be retrieved for the account.
    playlists = spotify_get_playlists(session, args.user)

    # 3. Retrieve all songs for each playlist found.
    if len(playlists) > 0:
        for playlist in tqdm(playlists, "[+] Downloading Playlists"):
            playlist.get_tracks(session)
        
        # Print resulting playlists
        for playlist in playlists:
            print(f"[+] Playlist: {playlist.name}, {len(playlist)} tracks")
    else:
        print(f"[!] No playlists downloaded")
        return

    # 4. Create a CSV formatted file to import into Excel
    with open(args.output, "w") as f:
        playlist_writer = csv.writer(f)

        for playlist in tqdm(playlists, f"[+] Writing playlists to {args.output}"):
            playlist.write_csv(playlist_writer)


# Ensures that if this is imported as a module the main() function is not
# called. Only called if run as a script.
if __name__ == '__main__':
    main()