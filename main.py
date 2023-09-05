from flask import Flask, Response, render_template, send_file, stream_with_context
import requests
import random
import pickle as pkl
import pycountry
import datetime as dt
import pytz

app = Flask(__name__)

with open('video_dict.pkl', 'rb') as f:
    feed_dict = pkl.load(f)

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

@app.route('/proxy/<path:url>')
def proxy(url):
    req = requests.get('http://' + url, stream=True)
    def generate():
        for chunk in req.iter_content(chunk_size=1024):
            yield chunk
    return Response(generate(), content_type=req.headers['content-type'])

@app.route('/')
def index():
    feed = random.randint(0, len(feed_dict) - 1)
    url = feed_dict[feed]['url']
    ip = ''.join(url.split('//')[-1]).split(':')[0]
    info = get_ip_info(ip)
    name = (info['city'] + ", " + info['region'] + ", " + pycountry.countries.get(alpha_2=info['country']).name).lower()
    org = info['org'].lower()
    timezone = pytz.timezone(info['timezone'])
    time = dt.datetime.now(timezone)
    loc = info['loc']
    print(info)
    X, Y = latlon_to_pixel(info['loc'])
    proxy_url = 'proxy/' + url.split('http://')[-1] 
    return render_template('index.html', name=name, url=proxy_url, info=info, time=time, ip=ip, org=org, loc=loc, X=X, Y=Y)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='7860', debug=True)
