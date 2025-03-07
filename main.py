from flask import Flask, Response, render_template, send_file, stream_with_context, request, session, redirect, url_for
import requests
import random
import pickle as pkl
import pycountry
import datetime as dt
import pytz
from io import BytesIO
import logging
import os 
import time

app = Flask(__name__)
app.secret_key = 'green-flounder'

with open('video_urls.pkl', 'rb') as f:
    live_urls = pkl.load(f)
    live_urls = [i for i in live_urls if i!= 'http://2.40.36.158:8084/img/video.mjpeg']
    live_urls[4161] = live_urls[1163]

with open('owner_dict.pkl', 'rb') as f:
    owner_dict = pkl.load(f)

from urllib.parse import urlsplit, urlunsplit, quote, parse_qsl, urlencode

def encode_url(url):
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qsl(query_string)
    encoded_query_params = [(key, quote(value)) for key, value in query_params]
    encoded_query_string = urlencode(encoded_query_params)
    finished = urlunsplit((scheme, netloc, path, encoded_query_string, fragment))
    return finished
    
from geolite2 import geolite2
def get_location(ip):
    start_time = time.time()  
    reader = geolite2.reader()
    location = reader.get(ip)
    geolite2.close()
    end_time = time.time()  

    elapsed_time = end_time - start_time

    if location:
        return {'country': location['country']['names']['en'] if 'country' in location else 'unknown country',
                'city': location['city']['names']['en'] if 'city' in location else 'unknown city',
                'region': location['subdivisions'][0]['names']['en'] if 'subdivisions' in location else 'unknown region',
                'loc': str(location['location']['latitude']) + ',' + str(location['location']['longitude']) if 'location' in location else '0,0',
                'timezone': location['location']['time_zone'] if 'location' in location and 'time_zone' in location['location'] else 'America/New_York'}
    else:
        return {'country': 'unknown country',
                'city': 'unknown city',
                'region': 'unknown region',
                'loc': str(0) + ',' + str(0),
                'timezone':'America/New_York'}
        

def latlon_to_pixel(loc):
    latitude = float(loc.split(',')[0])
    longitude = float(loc.split(',')[1])

    y = ((90-latitude)/180)
    x = ((longitude+180)/360)
    return x*100, y*100

from urllib.parse import urlparse, parse_qs

@app.route('/proxy/<path:url>')
def proxy(url): 
    start_time = time.time() 
    
    full_url = url
    query_string = request.query_string.decode("utf-8")
    if query_string:
        full_url += "?" + query_string

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Dnt': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }

    clean_url = full_url.replace('proxy/', '')
    clean_url = encode_url(clean_url)
    
    try:
        req = requests.get(clean_url, headers=headers, stream=True, timeout=1)

        end_time = time.time()  
        elapsed_time = end_time - start_time  

        return Response(req.iter_content(chunk_size=1024), content_type=req.headers['content-type'])

    except Exception as e:
        return Response("Error", status=500)


@app.route('/')
def index():
    id = request.args.get('id')
    if 'current_feed' in session and request.args.get('new', 'false') == 'false':
        feed = session['current_feed']
        url = live_urls[int(feed)]
    else:
        feed = random.randint(0, len(live_urls) - 1)
        url = live_urls[int(feed)]
        session['current_feed'] = feed
    
    if id:
        url = live_urls[int(id)]
        feed = id
        session['current_feed'] = id

    url = encode_url(url)
    url = url.replace('640x480','1280x960').replace('COUNTER','')
    
    id = feed
    ip = ''.join(url.split('//')[-1]).split(':')[0]
    info = get_location(ip)
    country = info['country'].lower()
    name = (info['city'] + ", " + info['region']).lower()
    page_title = (info['city'] + ", " + info['region'] + ", " + country).lower()
    timezone = pytz.timezone(info['timezone'])
    time = dt.datetime.now(timezone)
    time = time.strftime("%I:%M:%S %p")
    loc = info['loc']
    X, Y = latlon_to_pixel(info['loc'])
    proxy_url = 'proxy/' + url
    logging.info(f"Generated proxy URL: {proxy_url}")
    loc_link = f"https://www.google.com/maps/search/{loc}"
    ip_link = url
    try:
        owner = owner_dict[ip]
    except:
        owner = 'unknown'
    return render_template('index.html', 
                               name=name, 
                               url=encode_url(proxy_url), 
                               info=info, 
                               country=country, 
                               time=time, 
                               timezone=timezone,
                               ip=ip, 
                               ip_link=ip_link,
                               loc=loc, 
                               loc_link=loc_link, 
                               owner=owner,
                               X=X, 
                               Y=Y,
                               id=id,
                               page_title=page_title)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='7860')
