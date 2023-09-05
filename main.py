from flask import Flask, Response, render_template, send_file, stream_with_context, request, session
import requests
import random
import pickle as pkl
import pycountry
import datetime as dt
import pytz

app = Flask(__name__)
app.secret_key = 'green-flounder'

with open('video_dict.pkl', 'rb') as f:
    feed_dict = pkl.load(f)
    
with open('live_urls.pkl', 'rb') as f:
    live_urls = pkl.load(f)

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
    print('URL:', url)
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = requests.get(f'http://{url}', headers=headers, stream=True, timeout=15)
        content_type = req.headers['content-type']
        
        return Response(req.iter_content(chunk_size=10*1024), content_type=content_type)
        
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        return send_file('static/error.png', mimetype='image/png')

@app.route('/')
def index():
    if 'current_feed' in session and request.args.get('new', 'false') == 'false':
        feed = session['current_feed']
    else:
        feed = random.randint(0, len(live_urls) - 1)
        session['current_feed'] = feed
        
    #url = feed_dict[feed]['url']
    url = live_urls[feed]
    ip = ''.join(url.split('//')[-1]).split(':')[0]
    info = get_ip_info(ip)
    country = (pycountry.countries.get(alpha_2=info['country']).name).lower()
    name = (info['city'] + ", " + info['region'] + ", " + country).lower()
    org = info['org'].lower()
    timezone = pytz.timezone(info['timezone'])
    time = dt.datetime.now(timezone)
    loc = info['loc']
    X, Y = latlon_to_pixel(info['loc'])
    proxy_url = 'proxy/' + url.split('http://')[-1] 
    
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
    app.run(host='0.0.0.0', port='7860', debug=True)
