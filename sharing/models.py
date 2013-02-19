import bitly_api
import datetime

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import utc
from ourmy_app.models import Campaign, CampaignUser, Action


class SharingCampaign(models.Model):
    """ A one-to-one model of the Campaign that contains extra information only available in Sharing"""
    campaign = models.ForeignKey(Campaign, unique=True)
    post_text = models.CharField(max_length=120, help_text='The text you want to appear in social media posts before the link.', default="Check this out and spread the word!")
    long_url = models.URLField(default="http://www.youtube.com/user/CrewTide/featured?great")

    def __unicode__(self):
        return self.campaign.title + ' ' + self.long_url


class SharingCampaignUser(models.Model):
    """ For each campaign (which here is called a SharingCampaign), there can be many users. Each user
        gets their own sharable_url."""
    sharing_campaign = models.ForeignKey(SharingCampaign)
    user = models.ForeignKey(User)
    sharable_url = models.URLField()

    def __unicode__(self):
        return self.sharing_campaign.campaign.title + ' ' + self.user.last_name

    def save(self, *args, **kwargs):
        # only create a new bitly on new SharingCampaignUser objects.
        if not self.pk:
            connection = bitly_api.Connection(settings.BITLY_LOGIN, settings.BITLY_API_KEY)
            # we need to add a unique string to the end of this or all bitly links to this campaign will be the same.
            unique = User.objects.make_random_password()
            if '?' in self.sharing_campaign.long_url:
                url = self.sharing_campaign.long_url + '&ourmyun=' + unique
            else:
                url = self.sharing_campaign.long_url + '?ourmyun=' + unique
            
            result = connection.shorten(url)
            self.sharable_url = result["url"]
        super(SharingCampaignUser, self).save(*args, **kwargs)      # Call the "real" save() method.


class SharingAction(models.Model):
    """ A one-to-one model of the Action that contains extra information only available in Sharing. """
    FACEBOOK = 'FB'
    TWITTER = 'TW'
    SOCIAL_NETWORK_CHOICES = (
        (FACEBOOK, 'facebook'),
        (TWITTER, 'twitter'),
    )

    action = models.ForeignKey(Action)
    social_network = models.CharField(max_length=2, choices=SOCIAL_NETWORK_CHOICES, default=FACEBOOK)
    post_or_click = models.BooleanField()

    def is_post_or_click(self):
        if self.post_or_click:
            return "click"
        return "post"

    def __unicode__(self):
        return self.action.campaign.title + ': ' + self.get_social_network_display() + ', ' + self.is_post_or_click()


class SharingUserAction(models.Model):
    """ We create one of the 'post' SharingUserActions every time the user posts to a social network. 
        We create a 'click' SharingUserAction when there is a new bitly url."""
    user = models.ForeignKey(User)
    sharing_action = models.ForeignKey(SharingAction)
    created_at = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now().replace(tzinfo=utc))

    def __unicode__(self):
        return self.sharing_action.action.campaign.title + ': ' + self.sharing_action.social_network + ' by ' + self.user.username