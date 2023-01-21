from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.db.models import Avg, Max, Min, Q
from django.contrib.contenttypes.fields import GenericRelation

from videos.models import Video
from categories.models import Category
from ratings.models import Rating
from tags.models import TaggedItem
from djetflix.db.models import PublishStateOptions
from djetflix.db.receivers import publish_state_pre_save, unique_slugify_pre_save, slugify_pre_save


class PlaylistQuerySet(models.QuerySet):
    def published(self):
        now = timezone.now()
        return self.filter(
            publish_timestamp__lte=now,
            state=PublishStateOptions.PUBLISH
        )
    
    def movie_or_show(self):
        return self.filter(
            Q(type=Playlist.PlaylistTypeChoices.MOVIE) |
            Q(type=Playlist.PlaylistTypeChoices.SHOW)

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
    related = models.ManyToManyField("self", blank=True, related_name='related', through='PlaylistRelated')
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

    # class Meta:
    #     unique_together = (('title', 'slug'))

    def __str__(self):
        return self.title

    def get_related_items(self):
        return self.playlistrelated_set.all()

    def get_absolute_url(self):
        if self.is_movie:
            return f"/movies/{self.slug}/"
        if self.is_show:
            return f"/shows/{self.slug}/"
        if self.is_season and self.parent is not None:
            return f"/shows/{self.parent.slug}/seasons/{self.slug}/"
        return f"/playlists/{self.slug}/"

    @property
    def is_season(self):
        return self.type == self.PlaylistTypeChoices.SEASON

    @property
    def is_movie(self):
        return self.type == self.PlaylistTypeChoices.MOVIE

    @property
    def is_show(self):
        return self.type == self.PlaylistTypeChoices.SHOW

    def get_rating_avg(self):
        return Playlist.objects.filter(id=self.id).aggregate(Avg("ratings_value"))

    def get_rating_spread(self):
        return Playlist.objects.filter(id=self.id).aggregate(max=Max("ratings_value"), min=Min("ratings_value"))
    
    def get_short_display(self):
        return ""
    def get_video_id(self):
        """
        get main video id to render video for users
        """
        if self.video is None:
            return None
        return self.video.get_video_id()

    def get_clips(self):
        """
        get clips to render clips for users
        """
        return self.playlistitem_set.all().published()

    @property
    def is_published(self):
        return self.active
    
class MovieProxyManager(PlaylistManager):
    def all(self):
        return self.get_queryset().filter(type=Playlist.PlaylistTypeChoices.MOVIE)
class MovieProxy(Playlist):

    objects = MovieProxyManager()

    def get_movie_id(self):
        """
        get movie id to render movie for users
        """
        return self.get_video_id()

    class Meta:
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'
        proxy = True
    def save(self, *args, **kwargs):
        self.type = Playlist.PlaylistTypeChoices.MOVIE
        super().save(*args, **kwargs)
class TVShowProxyManager(PlaylistManager):
    def all(self):
        return self.get_queryset().filter(parent__isnull=True, type=Playlist.PlaylistTypeChoices.SHOW)
class TVShowProxy(Playlist):
    objects = TVShowProxyManager()
    class Meta:
        verbose_name = 'TV Show'
        verbose_name_plural = 'TV Shows'
        proxy = True
    def save(self, *args, **kwargs):
        self.type = Playlist.PlaylistTypeChoices.SHOW
        super().save(*args, **kwargs)
    @property
    def seasons(self):
        return self.playlist_set.published()
    def get_short_display(self):
        return f"{self.seasons.count()} Seasons"


class TVShowSeasonProxyManager(PlaylistManager):
    def all(self):
        return self.get_queryset().filter(parent__isnull=False, type=Playlist.PlaylistTypeChoices.SEASON)
class TVShowSeasonProxy(Playlist):
    objects = TVShowSeasonProxyManager()
    class Meta:
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'
        proxy = True
    def save(self, *args, **kwargs):
        self.type = Playlist.PlaylistTypeChoices.SEASON
        super().save(*args, **kwargs)

    def get_season_trailer(self):
        """
        get episodes to render for users
        """
        return self.get_video_id()

    def get_episodes(self):
        """
        get episodes to render for users
        """
        qs = self.playlistitem_set.all().published()
        print(qs)
        return qs




class PlaylistItemQuerySet(models.QuerySet):
    def published(self):
        now = timezone.now()
        return self.filter(
            playlist__state=PublishStateOptions.PUBLISH,
            playlist__publish_timestamp__lte= now,
            video__state=PublishStateOptions.PUBLISH,
            video__publish_timestamp__lte= now 
        )

class PlaylistItemManager(models.Manager):
    def get_queryset(self):
        return PlaylistItemQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()


class PlaylistItem(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = PlaylistItemManager()

    class Meta:
        ordering = ['order', '-timestamp']


def pr_limit_choices_to():
    return Q(type=Playlist.PlaylistTypeChoices.MOVIE) |  Q(type=Playlist.PlaylistTypeChoices.SHOW)


class PlaylistRelated(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    related = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='related_item', limit_choices_to=pr_limit_choices_to)
    order = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)



pre_save.connect(publish_state_pre_save, sender=TVShowProxy)
pre_save.connect(unique_slugify_pre_save, sender=TVShowProxy)
pre_save.connect(publish_state_pre_save, sender=TVShowSeasonProxy)
pre_save.connect(unique_slugify_pre_save, sender=TVShowSeasonProxy)
pre_save.connect(publish_state_pre_save, sender=MovieProxy)
pre_save.connect(unique_slugify_pre_save, sender=MovieProxy)
pre_save.connect(publish_state_pre_save, sender=Playlist)
pre_save.connect(unique_slugify_pre_save, sender=Playlist)