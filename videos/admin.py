from django.contrib import admin

from .models import Video, VideoProxy

class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_id']
    search_fields = ['title']
    # list_display = [ 'video_id']

    class Meta:
        model = Video


admin.site.register(Video, VideoAdmin)

class VideoProxyAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_id']
    search_fields = ['title']
    # list_display = [ 'video_id']

    def get_queryset(self, request):
        return VideoProxy.objects.filter(active=True)

    class Meta:
        model = VideoProxy


admin.site.register(VideoProxy, VideoProxyAdmin)

