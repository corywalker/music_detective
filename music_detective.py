#!/usr/bin/env python

'''
Takes song and artist names in the format:
    
Right Now (Na Na Na) - Akon
Beautiful Ft. Colby O'Donis... - Akon
I'm So Paid Ft. Lil' Wayne ... - Akon
Smooth Criminal - Alien Ant Farm
Nothin' On You (Feat. Bruno... - B.o.B.
Lights Go Down - Basement Jaxx
Public Enemy vs Benny Benas... - Benny Benassi
Money To Blow ft. Drake and... - Birdman
Forever (Main Version) - Chris Brown
Strangers In The Wind - Cut Copy
My Game (JS16 remix) - Darude
Memories (Featuring Kid Cudi) - David Guetta
United State of Pop 2009 - DJ Earworm

You can get these from Grooveshark by exporting a playlist as a widget and
copy + pasting.
'''

import os
import re
import urllib2
import operator
from urlparse import urlparse
from htmlentitydefs import name2codepoint

from BeautifulSoup import BeautifulSoup
from mutagen.mp3 import MP3
from mutagen.id3 import TPE1, TIT2, TALB, TCON, APIC

# for some reason, python 2.5.2 doesn't have this one (apostrophe)
name2codepoint['#39'] = 39

def unescape(s):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)

def amazon_search_url(query):
    base = 'http://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Ddigital-music-track&field-keywords='
    keywords = query.lower().replace(' ', '+')
    return base + keywords

def amazon_search_results(query):
    url = amazon_search_url(query)
    content = urllib2.urlopen(url).read()
    interesting_lines = []
    for line in content.split('\n'):
        if ('<td class="titleColOdd">' in line) or ('<td class="titleColEven">' in line):
            interesting_lines.append(line)
    results = []
    for line in interesting_lines:
        soup = BeautifulSoup(line)
        links = soup.findAll('a', href=True)
        # Use negative indexes because sometimes there is no preview link.
        new_song = Song(links[-3].string, links[-2].string, links[-1].string)
        new_song.link = links[-3]['href']
        album_path = urlparse(links[-1]['href']).path
        new_song.album_id = album_path.split('/')[-1]
        results.append(new_song)
    return results

def amazon_artwork(album_id):
    url = 'http://www.amazon.com/gp/product/images/' + album_id
    content = urllib2.urlopen(url).read()
    image = None
    for line in content.split('\n'):
        if '<div id="imageViewerDiv">' in line:
            soup = BeautifulSoup(line)
            image = soup.findAll('img', src=True)[0]
            break
    return image['src']
        
def clean_string(string):
    if not string:
        return None
    # Remove the unwanted featuring crap.
    cutoff_sequences = [' (', ' [', ' ft', ' Ft', ]
    for sequence in cutoff_sequences:
        string = string.split(sequence)[0]
    '''
    # Remove the elipsis if the string got cut off.
    if string[-3:] == '...':
        string = string[:-3]
    '''
    return string.strip()

def pretty_string(string):
    if not string:
        return 'unknown'
    return string

class Song:
    title = None
    artist = None
    album = None
    genre = None
    
    link = None
    album_id = None
    artwork = None
        
    def __init__(self, title=None, artist=None, album=None, genre=None):
        self.title = clean_string(title)
        self.artist = clean_string(artist)
        self.album = clean_string(album)
        self.genre = genre
        
    def from_string(self, string):
        try:
            title, artist = string.split(' - ')
        except ValueError:
            return False
        self.title = clean_string(title)
        self.artist = clean_string(artist)
        return True
        
    def get_title(self):
        return self.title
        
    def get_artist(self):
        return self.artist
    
    def get_album(self):
        if self.album == 'unresolved':
            return None
        if self.album:
            return self.album
        # First try searching by title and artist
        results = amazon_search_results(' '.join([self.get_title(), self.get_artist()]))
        if len(results):
            self.album = results[0].album
            self.album_id = results[0].album_id
            self.link = results[0].link
            return self.album
        '''
        # Search solely by name as a fallback
        results = amazon_search_results(self.title)
        if len(results):
            self.album = results[0].album
            self.album_id = results[0].album_id
            self.link = results[0].link
            return self.album
        '''
        '''
        manual_album = raw_input("What's the album of %s? " % self.fast_str())
        if manual_album:
            self.album = manual_album
            return self.album
        '''
        # This should be changed back to none if song info is changed.
        self.album = 'unresolved'
        return None
    
    def get_artwork(self):
        if self.artwork:
            return self.artwork
        if self.album_id:
            self.artwork = amazon_artwork(self.album_id)
            return self.artwork
        return None
    
    def get_genre(self):
        if self.genre:
            return self.genre
        if self.link:
            content = urllib2.urlopen(self.link).read()
            for line in content.split('\n'):
                if '<b>Genres:</b>' in line:
                    soup = BeautifulSoup(line)
                    genre_link = soup.findAll('a', href=True)[0]
                    self.genre = unescape(genre_link.string)
                    return self.genre
        return None
    
    def save_to_file(self, filename):
        audio = MP3(filename)
        if self.get_title():
            audio['TIT2'] = TIT2(3, self.get_title())
        if self.get_artist():
            audio['TPE1'] = TPE1(3, self.get_artist())
        if self.get_album():
            audio['TALB'] = TALB(3, self.get_album())
        if self.get_genre():
            audio['TCON'] = TCON(3, self.get_genre())
        if self.get_artwork():
            image_data = urllib2.urlopen(self.get_artwork()).read()
            audio['APIC'] = APIC(3, 'image/jpeg', 3, 'Front cover', image_data)
        audio.save()
    
    def fast_str(self):
        return str((self.title, self.artist))
            
    def __str__(self):
        return str((self.get_title(), self.get_artist(), self.get_album(), self.get_genre(), self.get_artwork()))

location = raw_input('Where are the files? ')
print 'Enter the song info and then "done":'

songs = []
while True:
    line = raw_input()
    if line == 'done':
        break
    curr_song = Song()
    if curr_song.from_string(line):
        songs.append(curr_song)
songs.reverse()

files_to_parse = []
for root, dirs, files in os.walk(location):
    for file in files:
        files_to_parse.append((root, file))
files_to_parse = sorted(files_to_parse, key=operator.itemgetter(1))
filenames = []
for my_file in files_to_parse:
    filenames.append(os.path.join(my_file[0], my_file[1]))
for filename in filenames:
    if not len(songs):
        break
    data = songs.pop()
    print filename, '<-', data
    data.save_to_file(filename)
