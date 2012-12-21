import bitly_api

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from ourmy_app.models import Campaign, CampaignUser, Action


class SharingCampaign(models.Model):
    """ A one-to-one model of the Campaign that contains extra information only available in Sharing"""
    campaign = models.ForeignKey(Campaign, unique=True)
    post_text = models.CharField(max_length=120, help_text='The text you want to appear in social media posts before the link.', default="Check this out and spread the word!")
    long_url = models.URLField(default="http://zoomtilt.com")

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
        connection = bitly_api.Connection(settings.BITLY_LOGIN, settings.BITLY_API_KEY)
        result = connection.shorten(self.sharing_campaign.long_url)
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

    action = models.ForeignKey(Action, unique=True)
    social_network = models.CharField(max_length=2, choices=SOCIAL_NETWORK_CHOICES, default=FACEBOOK)
    post_or_click = models.BooleanField()

    def __unicode__(self):
        return self.action.title + ' ' + self.social_network


class SharingUserAction(models.Model):
    """ We keep track of these SharingUserActions here to know how many times the user has posted. """
    user = models.ForeignKey(User)
    sharing_action = models.ForeignKey(SharingAction)

    def __unicode__(self):
        return self.sharing_action + ' by ' + self.user.username