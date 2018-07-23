#
#
# musicmerge.py: takes all the music from two spotify users public playlists and makes a playlist with
# all of the music that the two users share.
# requires: spotipy
#
#

# imports
import spotipy
import spotipy.util as util
import datetime as dt
import os


# globals
envp = "musicmerge_"
debug = False


def getenv(var):
    return os.getenv(envp+var)


def get_creds():
    user1_var = getenv("user1")
    user2_var = getenv("user2")
    client_id_var = getenv("clientid")
    client_secret_var = getenv("clientsecret")
    redirect_var = getenv("redirect")

    user1 = user1_var if user1_var else input("Enter user1 here (must have access to account): ")
    user2 = user2_var if user2_var else input("Enter user2 here: ")
    client_id = client_id_var if client_id_var else input("Enter client id for user1: ")
    client_secret = client_secret_var if client_secret_var else input("Enter client secret for user1: ")
    redirect = redirect_var if redirect_var else input("Enter authorized redirect_uri: ")
    return [user1, user2, util.prompt_for_user_token(user1, "playlist-modify-public", client_id, client_secret, redirect)]


def log(msg):
    print("[musicmerge "+str(dt.datetime.now())+"]" + " " + msg)


def get_playlists(sp_instance, user):
    user_playlists = sp_instance.user_playlists(user, 50)["items"]

    i = 1
    while len(user_playlists) == 50:
        user_playlists += sp_instance.user_playlists(user, 50, 50*i)
        i += 1

    return user_playlists


def get_playlist_uris(sp_instance, user1, user2):
    user1_playlists = get_playlists(sp_instance, user1)
    user2_playlists = get_playlists(sp_instance, user2)

    user1_playlist_uris = []
    user2_playlist_uris = []

    for i in user1_playlists:
        if type(i) is dict:
            user1_playlist_uris.append(i["uri"])

    for i in user2_playlists:
        if type(i) is dict:
            user2_playlist_uris.append(i["uri"])

    log("got " + str(len(user1_playlists)) + " from " + user1)
    log("got " + str(len(user2_playlists)) + " from " + user2)

    return [user1_playlist_uris, user2_playlist_uris]


def get_all_songs_user(sp_instance, user_playlists):
    user_songs = []
    for i in user_playlists:
        splitted = i.split(":")
        user = splitted[2]
        playlist_id = splitted[4]
        tracks_b = sp_instance.user_playlist_tracks(user, playlist_id)
        tracks = sp_instance.user_playlist_tracks(user, playlist_id)["items"]

        k = 1
        while len(tracks_b["items"]) == 100:
            tracks_b = sp_instance.user_playlist_tracks(user, playlist_id, offset=100*k)
            tracks += tracks_b["items"]
            k += 1

        for j in tracks:
            user_songs.append(j["track"]["uri"])

    return user_songs


def get_unique_songs(sp_instance, user1_playlists, user2_playlists):
    user1_songs = "" if debug else get_all_songs_user(sp_instance, user1_playlists)
    user2_songs = "" if debug else get_all_songs_user(sp_instance, user2_playlists)
    return [user1_songs, user2_songs]


def match_songs(user1_songs, user2_songs):
    matched_songs = []
    for i in user1_songs:
        if i in user2_songs:
            matched_songs.append(i)
    return matched_songs


def create_playlist_to_add(sp_instance,user):
    name = "Matched Playlist - " + str(dt.datetime.now())
    sp_instance.user_playlist_create(user, name)
    return name


def add_tracks(sp_instance, user, playlist_name, matched_songs):
    newest_playlist = get_playlists(sp_instance, user)[0]

    if not (newest_playlist["name"] == playlist_name):
        log("error: newest playlist not created one")
        exit(1)

    uri = newest_playlist["uri"]
    sp_instance.user_playlist_add_tracks(user, uri.split(":")[4], matched_songs)


def main():
    creds = get_creds()

    sp = spotipy.Spotify(auth=creds[2])

    playlists = get_playlist_uris(sp, creds[0], creds[1])

    unique_songs = get_unique_songs(sp, playlists[0], playlists[1])

    matched_songs = match_songs(unique_songs[0], unique_songs[1])

    new_playlist = create_playlist_to_add(sp, creds[0])

    add_tracks(sp, creds[0], new_playlist, matched_songs)


if __name__ == "__main__":
    main()
