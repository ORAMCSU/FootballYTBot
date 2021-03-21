import json
import pickle
import sys

import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube"]


def authenticate():
    api_service_name = "youtube"
    api_version = "v3"

    with open("ressources/CREDENTIALS_PICKLE_FILE", 'rb') as f:
        credentials = pickle.load(f)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)


def update_videos(id_video, title, description, tags):
    channel_list_response = youtube.channels().list(mine=True, part='statistics').execute()
    print(channel_list_response["items"][0]["statistics"])
    videos_list_response = youtube.videos().list(id=id_video, part="statistics").execute()
    print(videos_list_response["items"][0]["statistics"])
    videos_list_response = youtube.videos().list(id=id_video, part="snippet").execute()

    if not videos_list_response["items"]:
        print('Video "%s" was not found.' % id_video)
        sys.exit(1)

    videos_list_snippet = videos_list_response["items"][0]["snippet"]

    videos_list_snippet["title"] = title
    videos_list_snippet["description"] = description
    videos_list_snippet["tags"] = tags

    videos_update_response = (
        youtube.videos()
            .update(part="snippet", body=dict(snippet=videos_list_snippet, id=id_video))
            .execute()
    )


if __name__ == "__main__":

    with open("ressources/video_info.json", "r", encoding="utf-8") as file:
        dict_videos = json.load(file)

    for video_id in list(dict_videos.keys()):

        try:
            if len(dict_videos[video_id]["title"]) > 100:
                print(
                    f"Title too long -- {video_id} current length "
                    "{len(dict_videos[video_id]['title'])}"
                )
                exit()

            if len("\n".join(dict_videos[video_id]["description"])) > 5000:
                print(
                    f"Description too long -- {video_id} current length {len(' '.join(dict_videos[video_id]['description']))}"
                )
                exit()

            if len(", ".join(list(set(dict_videos[video_id]["tags"])))) > 500:
                print(
                    f"Tags too long -- {video_id} current length {len(' '.join(dict_videos[video_id]['tags']))}"
                )
                exit()

        except KeyError:
            pass

    youtube = authenticate()

    for video_id in list(dict_videos.keys())[:1]:
        update_videos(
            id_video=video_id,
            title=dict_videos[video_id]["title"],
            description="\n".join(dict_videos[video_id]["description"]),
            tags=list(set(dict_videos[video_id]["tags"])),
        )
