from flask import Flask, Response, render_template, send_file, stream_with_context, request, session, redirect, url_for
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

with open('active_urls.pkl', 'rb') as f:
    live_urls = pkl.load(f)

from io import BytesIO
url = 'https://storage.googleapis.com/bmllc-data-bucket/exceptions.pkl'
response = requests.get(url)
exceptions = pickle.loads(BytesIO(response.content).read())

live_urls = [i for i in live_urls if i not in exceptions]

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
    try:
        clean_url = url.replace('proxy/', '')
        print('Cleaned URL:', clean_url)
        
        req = requests.get(f'{clean_url}', headers=headers, stream=True, timeout=10)
        print("Status Code:", req.status_code)
        print("Response Headers:", req.headers)
        
        content_type = req.headers['content-type']
        
        return Response(req.iter_content(chunk_size=2*1024), content_type=content_type)
        
    except:
        print(f'Redirecting')
        exceptions.append(url)
        byte_stream = BytesIO()
        pickle.dump(exceptions, byte_stream)
        byte_stream.seek(0)
        url = 'https://storage.googleapis.com/bmllc-data-bucket/exceptions.pkl'
        response = requests.put(url, data=byte_stream.read())
        print(response)
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
    app.run(host='0.0.0.0', port='7860', debug=True)
