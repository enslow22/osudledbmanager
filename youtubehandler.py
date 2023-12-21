import datetime
import time
from googleapiclient.http import MediaFileUpload
from google_apis import create_service

# Big thanks to: Jie Jenn https://www.youtube.com/watch?v=xCYdddQrVV0&lc=UgwSvtqp8lKZ5sKNniV4AaABAg

class YoutubeHandler:

    def __int__(self):
        self.service = None

    def start_service(self):

        # See if service already running
        if self.service is not None:
            return

        API_NAME = 'youtube'
        API_VERSION = 'v3'
        SCOPES = ['https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/youtube.upload']
        client_file = 'client-secret.json'
        self.service = create_service(client_file, API_NAME, API_VERSION, SCOPES)

    # Uploads video to youtube and returns the video id.
    def upload_video(self, filename, title):

        if self.service is None:
            return False

        """
        Step 1. Upload Video
        """
        upload_time = (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat() + '.000Z'
        request_body = {
            'snippet': {
                'title': title,
                'description': 'www.osudle.com',
                'categoryId': '20',
                'tags': []
            },
            'status': {
                'privacyStatus': 'unlisted',
                'publishedAt': upload_time,
                'selfDeclaredMadeForKids': False
            },
            'notifySubscribers': False
        }

        video_file = 'danser/videos/%s' % filename
        media_file = MediaFileUpload(video_file)

        response_video_upload = self.service.videos().insert(
            part='snippet, status',
            body=request_body,
            media_body=media_file
        ).execute()
        uploaded_video_id = response_video_upload.get('id')
        print("%s uploaded to youtube at: %d" % (title, uploaded_video_id))


        """
        Step 3 (optional). Set video privacy status to "unlisted"
        """
        video_id = uploaded_video_id

        counter = 0
        response_update_video = self.service.videos().list(id=video_id, part='status').execute()
        update_video_body = response_update_video['items'][0]

        while 10 > counter:
            if update_video_body['status']['uploadStatus'] == 'processed':
                update_video_body['status']['privacyStatus'] = 'unlisted'
                self.service.videos().update(
                    part='status',
                    body=update_video_body
                ).execute()
                print('Video {0} privacy status is updated to "{1}"'.format(update_video_body['id'], update_video_body['status']['privacyStatus']))
                break
            # adjust the duration based on your video size
            time.sleep(10)
            response_update_video = self.service.videos().list(id=video_id, part='status').execute()
            update_video_body = response_update_video['items'][0]
            counter += 1

        return uploaded_video_id
