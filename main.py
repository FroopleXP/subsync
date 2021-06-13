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

scopes = ["https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret.json"


# Prompts a user to authenticate
def auth_user():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    return flow.run_console()


# Creates a YouTube client based on auth'd user creds
def get_yt_client(creds):
    return googleapiclient.discovery.build(
        api_service_name, api_version, credentials=creds)


# Gets all subscriptions for a user
def get_user_subs(yt_client):
    subscriptions = []
    next_page_token = None

    while True:
        subs_res = get_single_subs_page(
            yt_client, next_page_token=next_page_token)
        for sub in subs_res["items"]:
            subscriptions.append(sub["snippet"])
        if 'nextPageToken' in subs_res:
            next_page_token = subs_res["nextPageToken"]
        else:
            break
    return subscriptions


# Requests a single page of subscriptions
def get_single_subs_page(yt_client, next_page_token=None):
    sub_ls_req = yt_client.subscriptions().list(
        part="snippet", mine=True, pageToken=next_page_token, maxResults=50)
    return sub_ls_req.execute()


# Subscribe a user to a channel
def sub_to_channel(yt_client, sub):
    res = sub["resourceId"]
    sub_ins_req = yt_client.subscriptions().insert(
        part="snippet", body={"snippet": {"resourceId": res}})
    return sub_ins_req.execute()


# Commits the subscriptions
def commit_subs(yt_client, subs):
    for sub in subs:
        print("Subscribing to %s..." % (sub["title"]), end="\t")
        try:
            sub_to_channel(yt_client, sub)
            print("[Done]")
        except googleapiclient.errors.HttpError:
            print("[Fail]")


# Checks if a sub exists in a list of subs
# TODO: I think this can be optimized, it's the slowest part at the mo.
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


# Display title
def display_title(title):
    print("\n\n---\n%s\n=======================\n" % (title))


# Nicely displays a subscription to the user
def display_sub(sub):
    display_title(sub["title"])
    print(sub["description"])


# Display a minimal version of a subscription
def display_sub_min(sub):
    print("\t- %s" % (sub["title"]))


# Displays subs before commiting them
def display_sub_overview(subs):
    display_title("Subscription Overview")
    for sub in subs:
        display_sub_min(sub)


# Prompts the user to subscribe if they wish
def user_wants_sub_or_skip_rest(sub):
    display_sub(sub)
    inp = input("\nSubscribe to this channel? Y/n (s to skip rest): ")
    if inp:
        if inp == "n" or inp == "N":
            return (False, False)
        if inp == "s" or inp == "S":
            return (False, True)
    return (True, False)


# Prompts to user to commit or cancel subscriptions
def user_wants_to_commit_subs(subs):
    display_sub_overview(subs)
    inp = input(
        "\nWould you like to commit %s subscriptions? Y/n: " % (len(subs)))
    if not inp:
        return True
    return False


# Ask the user for the channels they want to sub to
def get_subs_user_wants(subs):
    channels_to_sub = []

    # Check if the user wants to sync all or pick
    all_or_pick_inp = input(
        "Sync all subscriptions or pick? A/p (A to sync all, p to pick):")
    if not all_or_pick_inp:  # Def.
        return subs
    if all_or_pick_inp != "p":  # Non-def. opt.
        return get_subs_user_wants(subs)

    for sub in subs:
        inp = user_wants_sub_or_skip_rest(sub)
        if inp[1]:  # Skip
            break
        if inp[0]:  # Yes
            channels_to_sub.append(sub)
    return channels_to_sub


def main():

    display_title("Authenticating user A")
    user_a_creds = auth_user()

    display_title("Authenticating user B")
    user_b_creds = auth_user()

    user_a_yt_client = get_yt_client(user_a_creds)
    user_b_yt_client = get_yt_client(user_b_creds)

    user_a_subs = get_user_subs(user_a_yt_client)
    user_b_subs = get_user_subs(user_b_yt_client)

    sub_diff = get_sub_diff(user_a_subs, user_b_subs)

    subs_user_wants = get_subs_user_wants(sub_diff)

    if user_wants_to_commit_subs(subs_user_wants):
        commit_subs(user_b_yt_client, subs_user_wants)


if __name__ == "__main__":
    main()
