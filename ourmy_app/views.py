from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ourmy_app.models import Campaign, Action, CampaignUser, UserActions
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
from django.template import loader
import datetime
import simplejson
from singly.singly import Singly
from urllib import urlencode
from ourmy_project.settings import SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET, SINGLY_REDIRECT_URI
from django.core import serializers
from django.conf import settings
import random
import bitly_api
from django import forms
from ourmy_app.forms import CampaignForm
from django.utils.functional import LazyObject


def index(request):
    # TODO: check that these are current campaigns
    current_campaign_list = Campaign.objects.all()
    return render_to_response('index.html', 
        {'campaign_list':current_campaign_list},
        context_instance=RequestContext(request))


def create_campaign(request):
    instance=None
    if request.method == 'POST':
        try:
            campaigns = Campaign.objects.filter(user=request.user)
            if campaigns.count() > 0:
                instance = campaigns[0]
            else:
                form = CampaignForm(request.POST)
        except:
            form = CampaignForm(request.POST)
        else:
            form = CampaignForm(request.POST, instance=instance)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.user = request.user
            import pdb; pdb.set_trace()
            campaign.save()
            return HttpResponseRedirect("/")
    else:
        try:
            campaigns = Campaign.objects.filter(user=request.user)
            if campaigns.count() > 0:
                campaign = campaigns[0]
            else:
                form = CampaignForm()
        except Campaign.DoesNotExist:
            form = CampaignForm()
        else:
            form = CampaignForm(instance=campaign)
    return render_to_response("create_campaign.html", {'form':form},
        context_instance=RequestContext(request))


def campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    services = [
        'facebook',
        # 'foursquare',
        # 'Instagram',
        # 'Tumblr',
        'twitter',
        #'LinkedIn',
        # 'FitBit',
        # 'Email'
    ]
 
    # import pdb; pdb.set_trace()
    if request.user.is_authenticated():
        try:
            user_profile = request.user.get_profile()
            # We replace single quotes with double quotes b/c of python's strict json requirements
            profiles = simplejson.loads(user_profile.profiles.replace("'", '"'))
        except:
            pass

    # create a CampaignUser object - this creates the unique bitly for this user for this campaign
    if isinstance(request.user, LazyObject):
        # user = User(first_name="anonymous", username="anonymous%d" % random.randrange(1,1000000))
        user, created = User.objects.get_or_create(first_name="anonymous")
        user.save()
    else:
        user = request.user
    
    campaign_user, created = CampaignUser.objects.get_or_create(user=user, campaign=campaign)
    campaign_user.save()

    users = User.objects.all()
    for user in users:
        user.points = random.randrange(1,100)
        # get all the actions this user has done

        user.points = 0
        user_actions = UserActions.objects.filter(user=user)
        # the user gets points for posting
        for user_action in user_actions:
            user.points += user_action.action.points_to_post
        # calculate points for each time their link was clicked
        # TODO: make this based on which social network it is
        connection = bitly_api.Connection(settings.BITLY_LOGIN, settings.BITLY_API_KEY)
        result = connection.clicks(campaign_user.bitly_url)
        # user.points += result["clicks"]*user_actions[0]
        # user.points += random.randrange(1,100)

    if request.method == 'POST':
        singly = Singly(SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET)
        user_profile = request.user.get_profile()

        try:
            access_token = user_profile.access_token
        except:
            return

        body = request.POST['body']
        url = request.POST['url']

        payload = {'access_token' : access_token, 
                   'services': 'facebook,twitter', 
                   'body': body, 
                   'url': url
                   }

        return_data = singly.make_request('/types/news', method='POST', request=payload)
        import pdb; pdb.set_trace()
        for service in services:
            try:
                success = return_data[service]['id']
                action, created = Action.objects.get_or_create(campaign=campaign, social_network=service)
                user_action = UserActions(user=request.user, action=action)
                user_action.save()
            except:
                pass

        # if they have posted, we create a UserAction for them and store it in the database
        # if success:

    response = render_to_response('campaign.html',
         { 'campaign':campaign, 'user':request.user, 'services':services, 'users':users, 'campaign_user':campaign_user },
         context_instance=RequestContext(request)
        )
    return response


def connect(request, template='connect.html'):
    services = [
        'Facebook',
        # 'foursquare',
        # 'Instagram',
        # 'Tumblr',
        'Twitter',
        'LinkedIn',
        # 'FitBit',
        # 'Email'
    ]
    if request.user.is_authenticated():
        user_profile = request.user.get_profile()
        # We replace single quotes with double quotes b/c of python's strict json requirements
        profiles = simplejson.loads(user_profile.profiles.replace("'", '"'))
    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )
    return response
