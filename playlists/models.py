from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.db.models import Avg, Max, Min
from django.contrib.contenttypes.fields import GenericRelation

from videos.models import Video
from categories.models import Category
from ratings.models import Rating
from tags.models import TaggedItem
from djetflix.db.models import PublishStateOptions
from djetflix.db.receivers import publish_state_pre_save, slugify_pre_save


class PlaylistQuerySet(models.QuerySet):
    def published(self):
        now = timezone.now()
        return self.filter(
            publish_timestamp__lte=now,
            state=PublishStateOptions.PUBLISH
        )


class PlaylistManager(models.Manager):
    def get_queryset(self):
        return PlaylistQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()
    
    def featured_playlists(self):
        return self.get_queryset().filter(type=Playlist.PlaylistTypeChoices.PLAYLIST)


class Playlist(models.Model):
    class PlaylistTypeChoices(models.TextChoices):
        MOVIE = "MOV", "Movie"
        SHOW = 'TVS', "TV Show"
        SEASON = 'SEA', "Season"
        PLAYLIST = 'PLY', "Playlist"

    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    order = models.IntegerField(default=1)
    title = models.CharField(max_length=220)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="playlists") 
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(blank=True, null=True)
    type = models.CharField(max_length=3, choices=PlaylistTypeChoices.choices, default=PlaylistTypeChoices.PLAYLIST)

    video = models.ForeignKey(Video, blank=True, null=True, on_delete=models.SET_NULL, related_name='featured_playlist')
    videos = models.ManyToManyField(Video, blank=True, related_name='playlist_item', through='PlaylistItem')

    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now=True)

    state = models.CharField(max_length=2, choices=PublishStateOptions.choices, default=PublishStateOptions.DRAFT)
    publish_timestamp = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    tags = GenericRelation(TaggedItem, related_query_name='playlist')
    ratings = GenericRelation(Rating, related_query_name='playlist')

    objects = PlaylistManager()

    def __str__(self):
        return self.title

    def get_avg_rating(self):
        return Playlist.objects.filter(id=self.id).aggregate(Avg("ratings_value"))

    def get_avg_spread(self):
        return Playlist.objects.filter(id=self.id).aggregate(max=Max("ratings_value"), min=Min("ratings_value"))

    @property
    def is_published(self):
        return self.active


pre_save.connect(publish_state_pre_save, sender=Playlist)

pre_save.connect(slugify_pre_save, sender=Playlist)


class MovieProxyManager(PlaylistManager):
    def all(self):
        return self.get_queryset().filter(type=Playlist.PlaylistTypeChoices.MOVIE)


class MovieProxy(Playlist):

    objects = MovieProxyManager()

    class Meta:
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'
        proxy = True

    def save(self, *args, **kwargs):
        self.type = Playlist.PlaylistTypeChoices.MOVIE
        super().save(*args, **kwargs)


class TVShowProxyManager(PlaylistManager):
    def all (self):
        return self.get_queryset().filter(parent__isnull=True, type=Playlist.PlaylistTypeChoices.SHOW)

class TVShowProxy(Playlist):

    objects = TVShowProxyManager()

    class Meta:
        verbose_name = 'TVShow Proxy'
        verbose_name = 'TVShow Proxies'
        proxy = True
    
    def save(self, *args, **kwargs):
        self.type = Playlist.PlaylistTypeChoices.SHOW
        super().save(*args, **kwargs)


class TVShowSeasonProxyManager(PlaylistManager):
    def all (self):
        return self.get_queryset().filter(parent__isnull=False, type=Playlist.PlaylistTypeChoices.SEASON)


class TVShowSeasonProxy(Playlist):
    objects = TVShowSeasonProxyManager()

    class Meta:
        verbose_name = 'Season Proxy'
        verbose_name = 'Seasons Proxies'
        proxy = True
    
    def save(self, *args, **kwargs):
        self.type = Playlist.PlaylistTypeChoices.SEASON
        super().save(*args, **kwargs)




class PlaylistItem(models.Model):
    playlist =models.ForeignKey(Playlist, on_delete=models.CASCADE)
    video =models.ForeignKey(Video, on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-timestamp']