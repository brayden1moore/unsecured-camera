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

with open('video_dict.pkl', 'rb') as f:
    feed_dict = pkl.load(f)
    
with open('live_urls.pkl', 'rb') as f:
    live_urls = pkl.load(f)

with open('active_urls.pkl', 'rb') as f:
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

def latlon_to_pixel(loc):
    latitude = float(loc.split(',')[0])
    longitude = float(loc.split(',')[1])

    y = ((90-latitude)/180)
    x = ((longitude+180)/360)
    return x*100, y*100

from urllib.parse import urlparse, parse_qs

@app.route('/proxy/<path:url>')
def proxy(url):
    session['exception_urls'] = load_exception_urls()
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
        print('\n\nREQUESTING URL:', clean_url)
        req = requests.get(clean_url, headers=headers, stream=True, timeout=15)
        logging.info(f"Status Code: {req.status_code}, Response Headers: {req.headers}")
        return Response(req.iter_content(chunk_size=2048), content_type=req.headers['content-type'])
        
    except:
        session['exception_urls'].append(url)
        save_exception_urls(session['exception_urls'])
        print('Added to exceptions:',session['exception_urls'])
        logging.error(f"Error in proxy.")
        return send_file('static/error.png', mimetype='image/png')


@app.route('/')
def index():
    session['exception_urls'] = load_exception_urls()
    
    if 'current_feed' in session and request.args.get('new', 'false') == 'false':
        feed = session['current_feed']
        url = live_urls[feed]
    else:
        while True:
            feed = random.randint(0, len(live_urls) - 1)
            url = live_urls[feed]
            if url not in session['exception_urls']:
                break
        session['current_feed'] = feed
        
    ip = ''.join(url.split('//')[-1]).split(':')[0]
    info = get_ip_info(ip)
    country = (pycountry.countries.get(alpha_2=info['country']).name).lower()
    name = (info['city'] + ", " + info['region'] + ", " + country).lower()
    org = info['org'].lower()
    timezone = pytz.timezone(info['timezone'])
    time = dt.datetime.now(timezone)
    loc = info['loc']
    X, Y = latlon_to_pixel(info['loc'])
    proxy_url = 'proxy/' + url
    
    loc_link = f"https://www.google.com/maps/search/{loc}"
    ip_link = url
    return render_template('index.html', 
                               name=name, 
                               url=proxy_url, 
                               info=info, 
                               country=country, 
                               time=time, 
                               ip=ip, 
                               ip_link=ip_link,
                               org=org, 
                               loc=loc, 
                               loc_link=loc_link, 
                               X=X, 
                               Y=Y)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='7860')
