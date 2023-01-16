
from .models import Playlist
from videos.models import Video

video_a = Video.objects.create(title='My title', video_id='asdasd')

playlist_a = Playlist.objects.create(title='This is my title', video=video_a)

