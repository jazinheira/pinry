import requests

from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models, transaction
from django.dispatch import receiver

from polymorphic.models import PolymorphicModel

from django_images.models import Image as BaseImage, Thumbnail
from taggit.managers import TaggableManager

from users.models import User


class ImageManager(models.Manager):
    _default_ua = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/48.0.2564.82 Safari/537.36',
    }

    # FIXME: Move this into an asynchronous task
    def create_for_url(self, url, referer=None):
        file_name = url.split("/")[-1].split('#')[0].split('?')[0]
        buf = BytesIO()
        headers = dict(self._default_ua)
        if referer is not None:
            headers["Referer"] = referer
        response = requests.get(url, headers=headers)
        buf.write(response.content)
        obj = InMemoryUploadedFile(buf, 'image', file_name,
                                   None, buf.tell(), None)
        # create the image and its thumbnails in one transaction, removing
        # a chance of getting Database into a inconsistent state when we
        # try to create thumbnails one by one later
        image = self.create(image=obj)
        for size in settings.IMAGE_SIZES.keys():
            Thumbnail.objects.get_or_create_at_size(image.pk, size)
        return image


class Image(BaseImage):
    objects = ImageManager()

    class Meta:
        proxy = True


class Pin(PolymorphicModel):
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(null=True)
    origin = models.URLField(null=True)
    referer = models.URLField(null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ForeignKey(Image, related_name='pin', on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager()

    def __unicode__(self):
        return '%s - %s' % (self.submitter, self.published)


@receiver(models.signals.post_delete, sender=Pin)
def delete_pin_images(sender, instance, **kwargs):
    instance.image.delete()

class WeddingDress(Pin):
    NECKLINES = (
        ('offsh', 'Off the Shoulder'),
        ('portrait', 'Portrait'),
        ('swthrt', 'Sweetheart'),
        ('sabrina', 'Sabrina'),
        ('halter', 'Halter'),
        ('scoop', 'Scoop'),
        ('jewel', 'Jewel'),
        ('vneck', 'V-Neck'),
        ('strapls', 'Strapless'),
    )
    DRESS_SIZES = (
        (0, '0'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (10, '10'),
        (11, '11'),
        (12, '12'),
        (13, '13'),
        (14, '14'),
        (15, '15'),
    )
    SILHOUETTES = (
        ('ball', 'Ball Gown'),
        ('aline', 'A-Line'),
        ('fitflare', 'Fit and Flare'),
        ('mermaid', 'Mermaid'),
        ('sheath', 'Sheath'),
        ('trumpet', 'Trumpet'),
        ('peplum', 'Peplum'),
    )
    HEIGHTS = (
        ('under5', '< 5'),
        ('5to54', '5 - 5.4'),
        ('54to58', '5.4 - 5.8'),
        ('58to6', '5.8 - 6'),
        ('over6', '> 6'),
    )

    style = models.CharField(max_length=30)
    #materials = TaggableManager(related_name='materials')
    neckline = models.CharField(
        max_length=8,
        choices=NECKLINES,
    )
    size = models.CharField(
        choices=DRESS_SIZES,
    )
    silhouette = models.CharField(
        max_length=8,
        choices=SILHOUETTES,
    )
    height = models.CharField(
        max_length=8,
        choices=HEIGHTS,
    )



