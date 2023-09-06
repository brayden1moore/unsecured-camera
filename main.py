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

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'green-flounder'

with open('video_urls.pkl', 'rb') as f:
    live_urls = pkl.load(f)

def load_exception_urls():
    url = os.environ['EXCEPTIONS']
    response = requests.get(url)
    return pkl.loads(response.content)

def save_exception_urls(exception_urls):
    url = os.environ['EXCEPTIONS']
    data = pkl.dumps(exception_urls)
    requests.put(url, data=data)
    
def get_ip_info(ip_address):
    try:
        response = requests.get(f"http://ipinfo.io/{ip_address}/json")
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}

from geolite2 import geolite2
def get_location(ip):
    reader = geolite2.reader()
    location = reader.get(ip)
    geolite2.close()
    if location:
        return {'country': location['country']['names']['en'],
                'city': location['city']['names']['en'] if 'city' in location else '',
                'region': location['subdivisions'][0]['names']['en'] if 'subdivisions' in location else '',
                'loc': str(location['location']['latitude']) + ',' + str(location['location']['longitude']),
                'timezone': location['location']['time_zone'] if 'time_zone' in location['location'] else 'America/New_York'}

def latlon_to_pixel(loc):
    latitude = float(loc.split(',')[0])
    longitude = float(loc.split(',')[1])

    y = ((90-latitude)/180)
    x = ((longitude+180)/360)
    return x*100, y*100

from urllib.parse import urlparse, parse_qs

@app.route('/proxy/<path:url>')
def proxy(url):

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

    clean_url = url.replace('proxy/', '')
    
    try:
        logging.info(f"Sending request to: {clean_url}")
        req = requests.get(clean_url, headers=headers, stream=True, timeout=5)
        logging.info(f"Status Code: {req.status_code}, Response Headers: {req.headers}")
        return Response(req.iter_content(chunk_size=2048), content_type=req.headers['content-type'])
    
    except Exception as e:
        logging.error(f"Error in proxy: {str(e)}")
        print('Skipped')
        return redirect(url_for('index', new='true'))
        #return send_file('static/error.png', mimetype='image/png')


@app.route('/')
def index():
    
    if 'current_feed' in session and request.args.get('new', 'false') == 'false':
        feed = session['current_feed']
        url = live_urls[feed]
    else:

        feed = random.randint(0, len(live_urls) - 1)
        url = live_urls[feed]
        session['current_feed'] = feed
        
    ip = ''.join(url.split('//')[-1]).split(':')[0]
    print('IP:',ip)
    info = get_location(ip)
    country = info['country'].lower()
    name = (info['city'] + ", " + info['region'] + ", " + country).lower()
    timezone = pytz.timezone(info['timezone'])
    time = dt.datetime.now(timezone)
    time = time.strftime("%I:%M:%S %p")
    loc = info['loc']
    X, Y = latlon_to_pixel(info['loc'])
    proxy_url = 'proxy/' + url
    logging.info(f"Generated proxy URL: {proxy_url}")
    loc_link = f"https://www.google.com/maps/search/{loc}"
    ip_link = url
    return render_template('index.html', 
                               name=name, 
                               url=proxy_url, 
                               info=info, 
                               country=country, 
                               time=time, 
                               timezone=timezone,
                               ip=ip, 
                               ip_link=ip_link,
                               loc=loc, 
                               loc_link=loc_link, 
                               X=X, 
                               Y=Y)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='7860')
