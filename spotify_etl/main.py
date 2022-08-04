import requests
import base64
import datetime
import json
import os
import pandas as pd

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = 'https://accounts.spotify.com/api/token'
    base_url = 'https://api.spotify.com/v1'

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        """
        Returns a base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f'{client_id}:{client_secret}'
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
    
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            'Authorization': f'Basic {client_creds_b64}',
            'Content-Type':'application/x-www-form-urlencoded'
    }
    
    def get_token_data(self):
        return {
            'grant_type':'client_credentials'
    }
               
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r =requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Authentication falied")
        data = r.json()
        access_token = data['access_token']
        expires_in = data['expires_in']
        expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < datetime.datetime.now()
        return True
    
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now or token == None:
            self.perform_auth()
            return self.get_access_token()
        return token
    
    def get_resource_headers(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization" : f"Bearer {access_token}"
        }
        return headers
    
    def get_resource(self, lookup_id, resource_type='albums', comp=''):
        endpoint = f'{self.base_url}/{resource_type}/{lookup_id}{comp}'
        headers = self.get_resource_headers()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()
    
    def get_playlist_items(self, query):
        _id = self.base_search(query)
        data = self.get_resource(_id, resource_type='playlists', comp='/tracks')
        return [(data['items'][i]['track']['id']) for i, _ in enumerate(data['items'])]

    def get_audio_features(self, sentiment, query):
        dicio={}
        lista = self.get_playlist_items(query)
        base_df = pd.DataFrame()
        for i,_ in enumerate(lista):
            _id = lista[i]
            data = self.get_resource(_id, resource_type='audio-features')
            if not data:
                track_df = pd.DataFrame()
                playlist_df = pd.concat([base_df,track_df])
            else:
                dicio[data['id']]={
                    'danceability':data['danceability'],
                    'energy':data['energy'],
                    'tempo':data['tempo'],
                    'loudness':data['loudness'],
                    'mode':data['mode'],
                    'valence':data['valence'],
                    'mood':sentiment
                }
                track_df = pd.DataFrame(dicio).T
                playlist_df = pd.concat([base_df,track_df])
        return playlist_df

    def base_search(self, query, search_type='playlist'):
        headers = self.get_resource_headers()
        endpoint = f'{self.base_url}/search'
        data = {'q' : query.lower(), 'type' : search_type.lower()}
        r = requests.get(endpoint, params=data, headers=headers)
        if r.status_code not in range (200,299):
            return {}
        return r.json()['playlists']['items'][0]['id']

    def run(self):
        dicio={}
        self.df = pd.DataFrame(dicio, columns=['danceability','energy','tempo','loudness','mode','valence','mood'])
        with open('config.json') as fp:
            infos = json.load(fp)
        for i in infos:
            for j in infos[i]:
                self.df = pd.concat([self.get_audio_features(sentiment=i,query=j), self.df])
        self.df.to_csv('datalake/data.csv')
   
spotify = SpotifyAPI(client_id, client_secret)

if __name__ == '__main__':
    spotify.run()
