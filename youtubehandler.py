import datetime
import time
from googleapiclient.http import MediaFileUpload
from google_apis import create_service

# Big thanks to: Jie Jenn https://www.youtube.com/watch?v=xCYdddQrVV0&lc=UgwSvtqp8lKZ5sKNniV4AaABAg

class YoutubeHandler:

    def __init__(self):
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

        media_file = MediaFileUpload(filename)

        response_video_upload = self.service.videos().insert(
            part='snippet, status',
            body=request_body,
            media_body=media_file
        ).execute()
        uploaded_video_id = response_video_upload.get('id')
        print("%s uploaded to youtube at: https://youtu.be/%s" % (title, uploaded_video_id))
        return 'https://youtu.be/'+uploaded_video_id
