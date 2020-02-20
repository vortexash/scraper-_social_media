# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 20:34:48 2020

@author: Ashish
"""

import pandas as pd
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import json
from pandas.io.json import json_normalize
import numpy as np
import requests
import praw
import re
import tweepy


class scraper:   
    def __init__(self): 
        pass
    def instagram_scrapy(self,hashtag):
        hashtag=hashtag
        browser = Chrome()
        source=browser.get('https://www.instagram.com/explore/tags/'+hashtag)
        links=[]
        source = browser.page_source
        data=bs(source, 'html.parser')
        body = data.find('body')
        script = body.find('script', text=lambda t: t.startswith('window._sharedData'))
        page_json = script.text.split(' = ', 1)[1].rstrip(';')
        data = json.loads(page_json)
        for link in data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']:
            links.append('https://www.instagram.com'+'/p/'+link['node']['shortcode']+'/')
        result=pd.DataFrame()
        for i in range(len(links)):
            try:
                page = urlopen(links[i]).read()
                data=bs(page, 'html.parser')
                body = data.find('body')
                script = body.find('script')
                raw = script.text.strip().replace('window._sharedData =', '').replace(';', '')
                json_data=json.loads(raw)
                posts =json_data['entry_data']['PostPage'][0]['graphql']
                posts= json.dumps(posts)
                posts = json.loads(posts)
                x = pd.DataFrame.from_dict(json_normalize(posts), orient='columns') 
                x.columns =  x.columns.str.replace("shortcode_media.", "")
                result=result.append(x)

            except:
                np.nan
        #Just check for the duplicates
        result = result.drop_duplicates(subset = 'shortcode')
        result.index = range(len(result.index))
        result=result.drop(['display_resources','caption_is_edited','commenting_disabled_for_viewer','comments_disabled','dash_info.is_dash_eligible','dash_info.number_of_qualities','dash_info.video_dash_manifest','dimensions.height','dimensions.width','edge_media_preview_comment.count','edge_media_preview_comment.edges','edge_media_preview_like.count','edge_media_preview_like.edges','edge_media_to_parent_comment.count','edge_media_to_parent_comment.edges','edge_media_to_parent_comment.page_info.end_cursor','edge_media_to_parent_comment.page_info.has_next_page','edge_media_to_sponsor_user.edges','edge_media_to_tagged_user.edges','edge_sidecar_to_children.edges','edge_web_media_to_related_media.edges','encoding_status','fact_check_information','fact_check_overall_rating','gating_info','has_ranked_comments','id','is_ad','is_published','is_video','location','location.address_json','location.has_public_page','location.id','location.name','location.slug','media_preview','owner.blocked_by_viewer','owner.followed_by_viewer','owner.full_name','owner.has_blocked_viewer','owner.id','owner.is_private','owner.is_unpublished','owner.is_verified','owner.profile_pic_url','owner.requested_by_viewer','owner.restricted_by_viewer','owner.username','product_type','shortcode','taken_at_timestamp','thumbnail_src','title','tracking_token','video_duration','video_url','video_view_count','viewer_can_reshare','viewer_has_liked','viewer_has_saved','viewer_has_saved_to_collection','viewer_in_photo_of_you'],axis=1)
        lis=[]
        for k in range(len(result['edge_media_to_caption.edges'])): 
            lis.append([i for i in result['edge_media_to_caption.edges'].iloc[k][0]['node']['text'].split(' ')if i.startswith('#')])
        result['hashtags']=lis
        result.drop(['edge_media_to_caption.edges'],axis=1,inplace=True)
        return result
    def clean_data(self,bioList, column_name = 'description'):
        clean_b = [re.sub('[^a-zA-Z ,.!?]+', '', str(b)) for b in np.array(bioList[column_name])]
        clean_b = [re.sub(r"(https?:\/\/|www.)(.*?|\/)(?=\s|$)\s*", ' ', q) for q in clean_b]
        clean_b = [re.sub(r"([,.?!~`@=+$#%^&*_;:\"'\|\n\b\s\t\-\(\)\[\]]+)\1", ' ', q) for q in clean_b]
        clean_b = [re.sub('\s+', ' ', q.strip()) for q in clean_b]
        bioList[column_name] = clean_b
        return bioList
    def youtube_scraper(self):
        source = requests.get("https://www.youtube.com/feed/trending").text
        soup = bs(source, 'lxml')
        final_val={}
        for content in soup.find_all('div', class_= "yt-lockup-content"):
            try:
                title = content.h3.a.text
        #         print(title)
                description = content.find('div', class_="yt-lockup-description yt-ui-ellipsis yt-ui-ellipsis-2").text
        #         print(description)
                final_val[title]=description
    
            except Exception as e:
                description = None
    
        df = pd.DataFrame.from_dict(final_val, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index':'Title',0:'Description'},inplace=True)
        data2=self.clean_data(df,'Title')
        return data2
    def reddit_scraper(self):
        reddit = praw.Reddit(client_id='as3sU0s4MI_5zg', client_secret='8OftB2B7mPznbLsifIpfEUClYhg', user_agent='scraper_trending')
        posts = []
        ml_subreddit = reddit.subreddit('all')
        for post in ml_subreddit.hot(limit=100):
            posts.append([post.title, post.subreddit, post.url])
        posts = pd.DataFrame(posts,columns=['title', 'subreddit', 'url'])
        data3=self.clean_data(posts,'title')
        return data3
    def twitter_hashtags(self):
        consumer_key = 'Wl5FFomIWu0Ys0U0IwkmCrBHn'
        consumer_secret = 'RGiCnp2QGnfBvY56LE0qy0v0xnvfNiUDy9IzZITXKZCbgIbzrT'
        access_token = '1202611314192859136-CyhwuTPWkCUzaivwozHF9NoWiQIU0C'
        access_token_secret = 'y0FJszNhBv0kcWKux3TUfwYJTQ7Be4nrJDMEYPJN7cHdf'
    
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth) 
        ID = 1 
        d = {}
        trends = api.trends_place(ID)
        trends = json.loads(json.dumps(trends, indent=1))
        for trend in trends[0]["trends"]:
             d[trend['name']]=trend['url']
        df=pd.DataFrame.from_dict(d,orient='index')
        df.reset_index(level=0, inplace=True)
        df.rename(columns={'index':'hashtags',0:'links'},inplace=True)
        return df

