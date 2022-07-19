import discord
import os
import requests
import json
import random
from bs4 import BeautifulSoup

client = discord.Client()
my_secret = os.environ['TOKEN']
VAGALUME_KEY = os.environ['VAGALUME_KEY']

def get_quote(art):
  songs = get_songs(art)
  name = ' '.join([name.capitalize() for name in art.split('-')])
  mus = random.choice(songs)
  url = f"https://api.vagalume.com.br/search.php?art={art}&mus={mus}&apikey={VAGALUME_KEY}"
  response = requests.get(url)
  json_data = json.loads(response.text)
  music = json_data['mus'][0]['text']
  verses = music.split("\n\n")
  verse = random.choice(verses).split("\n")
  j = random.randrange(0, (len(verse)-1))
  quote = f"'{verse[j]}\n{verse[j+1]}' -{name}"
  return quote

def get_songs(art):
  url=f'https://www.vagalume.com.br/{art}/'
  response = requests.get(url)
  html = response.text
  soup = BeautifulSoup(html, 'html.parser')
  songs = [item.get('href')[(len(art)+1):].strip('.html').strip('/') for item in soup.find_all('a', class_='nameMusic')]
  return songs

def get_artist(artist):
  url_request = f'https://api.vagalume.com.br/search.art?apikey={VAGALUME_KEY}&q={artist}&limit=5'
  response2 = requests.get(url_request)
  json_data2 = json.loads(response2.text)
  art = json_data2['response']['docs'][0]['url'].strip('/')
  return get_quote(art=art)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
@client.event
async def on_message(message):
  if message.author == client.user:
    return
   
  msg = message.content 
 
  if msg.startswith('!quote'):
    artist = msg.split('!quote ',1)[1]
    quote = get_artist(artist)
    await message.channel.send(quote)


if __name__=='__main__':
  client.run(my_secret)
