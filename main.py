'''
    SubSync
    --------------
    Synchronises YouTube subscriptions between two channels.
'''

import os
from re import sub

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret.json"


# Prompts a user to authenticate
def auth_user():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    return flow.run_console()


# Gets all subscriptions for a user
def get_user_subs(creds):
    subscriptions = []
    next_page_token = None

    while True:
        subs_res = get_single_subs_page(creds, next_page_token=next_page_token)
        for sub in subs_res["items"]:
            subscriptions.append(sub["snippet"])
        if 'nextPageToken' in subs_res:
            next_page_token = subs_res["nextPageToken"]
        else:
            break
    return subscriptions


# Requests a single page of subscriptions
def get_single_subs_page(creds, next_page_token=None):
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=creds)
    sub_request = youtube.subscriptions().list(
        part="snippet,contentDetails", mine=True, pageToken=next_page_token, maxResults=50)
    return sub_request.execute()


# Checks if a sub exists in a list of subs
def sub_exists_in_subs(sub, subs):
    chan_id = sub["resourceId"]["channelId"]
    exists = False
    for _sub in subs:
        if _sub["resourceId"]["channelId"] == chan_id:
            exists = True
    return exists


# Get the subscriptions that user A has that user B doesn't
def get_sub_diff(user_a_subs, user_b_subs):
    diff = []
    for sub in user_a_subs:
        if not sub_exists_in_subs(sub, user_b_subs):
            diff.append(sub)
    return diff


# Nicely displays a subscription to the user
def display_sub(sub):
    print("%s\n====\n\t%s\n" % (sub["title"], sub["description"]))


# Display a minimal version of a subscription
def display_sub_min(sub):
    print("\t- %s" % (sub["title"]))


# Prompts the user to subscribe if they wish
def user_wants_sub_or_skip_rest(sub):
    display_sub(sub)
    inp = input("Subscribe to this channel? Y/n (s to skip rest): ")
    if inp:
        if inp == "n" or inp == "N":
            return (False, False)
        if inp == "s" or inp == "S":
            return (False, True)
    return (True, False)


# Ask the user for the channels they want to sub to
def get_subs_user_wants(subs):
    channels_to_sub = []
    for sub in subs:
        inp = user_wants_sub_or_skip_rest(sub)
        if inp[1]:  # Skip
            break
        if inp[0]:  # Yes
            channels_to_sub.append(sub)
    return channels_to_sub


def main():
    user_a_creds = auth_user()
    user_b_creds = auth_user()

    user_a_subs = get_user_subs(user_a_creds)
    user_b_subs = get_user_subs(user_b_creds)

    print("Total user A subs %i\nTotal user B subs %i" %
          (len(user_a_subs), len(user_b_subs)))

    sub_diff = get_sub_diff(user_a_subs, user_b_subs)

    print("Total diff %i" % (len(sub_diff)))

    subs_user_wants = get_subs_user_wants(sub_diff)

    for sub in subs_user_wants:
        display_sub_min(sub)


if __name__ == "__main__":
    main()
