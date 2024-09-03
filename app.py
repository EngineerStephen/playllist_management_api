from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import asc, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import List

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Mysql24$@localhost/LDMusic'
db = SQLAlchemy(app)

# Set up session maker and session object
Session = sessionmaker(bind=db.engine)
session = scoped_session(Session)

# SCHEMAS for songs and playlist 
class SongSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    genre = fields.String(required=True, validate=validate.Length(min=1, max=100))
    artist = fields.String(required=True, validate=validate.Length(min=1, max=100))

    class Meta:
        fields = ("name", "genre", "artist")

class PlaylistSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    genre = fields.String(required=True, validate=validate.Length(min=1, max=100))

    class Meta:
        fields = ("name", "genre", "artist")

# MODELS
class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)

    playlists = db.relationship('Playlist', secondary='playlist_songs', back_populates='songs')

class Playlist(db.Model):
    __tablename__ = 'playlists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255))
    artist = db.Column(db.String(255))

    songs = db.relationship('Song', secondary='playlist_songs', back_populates='playlists')

class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'

    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), primary_key=True)

# ENDPOINTS for songs and playlist
# Route to create a new song
@app.route("/songs", methods=["POST"])
def create_songs():
    song_data = request.json
    
    try:
        validated_data = SongSchema().load(song_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_song = Song(
        name=validated_data['name'],
        genre=validated_data['genre'],
        artist=validated_data['artist']
    )
    db.session.add(new_song)
    db.session.commit()
    
    return jsonify({"message": f"{new_song.name} added successfully"}), 201

# Route to update a song
@app.route("/songs", methods=["PUT"])
def update_songs():
    song_data = request.json
    song_name = request.args.get('name')
    
    try:
        validated_data = SongSchema().load(song_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    song = session.get(Song, song_name)
    if song is None:
        return jsonify({"message": "Song not found"}), 404
    
    song.name = validated_data['name']
    song.genre = validated_data['genre']
    song.artist = validated_data['artist']
    db.session.commit()
    
    return jsonify({"message": f"{song.name} updated successfully"}), 200

# Route to delete a song
@app.route("/songs", methods=["DELETE"])
def delete_songs():
    song_name = request.args.get('name')
    
    song = session.get(Song, song_name)
    if song is None:
        return jsonify({"message": "Song not found"}), 404
    
    db.session.delete(song)
    db.session.commit()
    
    return jsonify({"message": f"{song.name} deleted successfully"}), 200

# Route to get a song   
@app.route("/songs", methods=["GET"])
def get_songs():
    song_name = request.args.get('name')
    
    song = session.get(Song, song_name)
    if song is None:
        return jsonify({"message": "Song not found"}), 404
    
    return jsonify({"name": song.name, "genre": song.genre, "artist": song.artist}), 200

# Create a playlist
@app.route("/playlists", methods=["POST"])
def create_playlist():
    playlist_data = request.json
    
    try:
        validated_data = PlaylistSchema().load(playlist_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_playlist = Playlist(
        name=validated_data['name'],
        genre=validated_data.get('genre'),
        artist=validated_data.get('artist')
    )
    db.session.add(new_playlist)
    db.session.commit()
    
    return jsonify({"message": f"{new_playlist.name} added successfully"}), 201

# Route to update a playlist
@app.route("/playlists", methods=["PUT"])
def update_playlist():
    playlist_data = request.json
    playlist_name = request.args.get('name')
    
    try:
        validated_data = PlaylistSchema().load(playlist_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    playlist = session.get(Playlist, playlist_name)
    if playlist is None:
        return jsonify({"message": "Playlist not found"}), 404
    
    playlist.name = validated_data['name']
    playlist.genre = validated_data.get('genre')
    playlist.artist = validated_data.get('artist')
    db.session.commit()
    
    return jsonify({"message": f"{playlist.name} updated successfully"}), 200

# Route to delete a playlist
@app.route("/playlists", methods=["DELETE"])
def delete_playlist():
    playlist_name = request.args.get('name')
    
    playlist = session.get(Playlist, playlist_name)
    if playlist is None:
        return jsonify({"message": "Playlist not found"}), 404
    
    db.session.delete(playlist)
    db.session.commit()
    
    return jsonify({"message": f"{playlist.name} deleted successfully"}), 200

# Route to add a song to a playlist
@app.route("/playlists/add_song", methods=["POST"])
def add_playlist_song():
    playlist_name = request.args.get('playlist_name')
    song_name = request.args.get('song_name')
    
    playlist = session.get(Playlist, playlist_name)
    song = session.get(Song, song_name)
    
    if playlist is None:
        return jsonify({"message": "Playlist not found"}), 404
    if song is None:
        return jsonify({"message": "Song not found"}), 404
    
    playlist.songs.append(song)
    db.session.commit()
    
    return jsonify({"message": f"{song.name} added to {playlist.name} successfully"}), 200

# Route to remove a song from a playlist
@app.route("/playlists/remove_song", methods=["DELETE"])
def remove_playlist_song():
    playlist_name = request.args.get('playlist_name')
    song_name = request.args.get('song_name')
    
    playlist = session.get(Playlist, playlist_name)
    song = session.get(Song, song_name)
    
    if playlist is None:
        return jsonify({"message": "Playlist not found"}), 404
    if song is None:
        return jsonify({"message": "Song not found"}), 404
    
    playlist.songs.remove(song)
    db.session.commit()
    
    return jsonify({"message": f"{song.name} removed from {playlist.name} successfully"}), 200

# Sort songs in playlist by name, genre, artist
@app.route("/playlists/sort", methods=["GET"])
def sort_playlist_songs():
    playlist_name = request.args.get('name')
    
    playlist = session.get(Playlist, playlist_name)
    if playlist is None:
        return jsonify({"message": "Playlist not found"}), 404

    sorted_songs = session.query(Song).join(Playlist.songs).filter(Playlist.id == playlist.id).order_by(asc(Song.name), desc(Song.artist), desc(Song.genre)).all()
    
    sorted_songs_data = [{"name": song.name, "genre": song.genre, "artist": song.artist} for song in sorted_songs]
    
    return jsonify(sorted_songs_data), 200
