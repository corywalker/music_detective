#!/usr/bin/env python

import os
import operator
from musichelpers import Song

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

