# -*- coding: utf-8 -*-
import discord_user
import discord
import asyncio
import re
import requests
import html
from string import Template
from flask import Flask,make_response, render_template
from diskcache import Cache

cache = Cache('/tmp/rsscache')

rss_length=15

app = Flask(__name__)
client = discord.Client()

@app.route("/actualites.xml")
def hello():
    #del cache[b'items']
    if b'items' not in cache:
        if not b'get_items' in cache:
            cache.set(b'items',getItems(),expire=600)
        else:
            import time
            while b'get_items' in cache:
                time.sleep(5)
    items = cache[b'items']

    #items = "".join([item.substitute(it) for it in items])
    #rssflux = flux.substitute(items=items,link="https://discordapp.com/channels/254215611264008192/256392899720249344").encode('utf8')

    return render_template('rss.html',items=items,link="https://discordapp.com/channels/254215611264008192/256392899720249344"), 200, {'Content-Type': 'application/rss+xml; charset=utf-8'}
    #return Response(response=rssflux, status=200, mimetype="application/rss+xml")

def getItems():
    cache.set(b'get_items',True,expire=180)
    client = discord.Client()

    def getmeta(t,property):
        import re
        g = re.search(r'<meta property="'+property+'"[^>]*content="([^"]+)"',t)
        if g:
            return html.unescape(g.groups()[0])
        else:
            return ""

    @client.event
    async def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')


        channel = client.get_channel('256392899720249344')
        async for msg in client.logs_from(channel,limit=rss_length):
            link = re.search(r'(https?:[^ \n]+)',msg.content)
            if link:
                link = link.groups()[0]
                r = requests.get(link)
                c = r.content.decode('utf8')
                title = getmeta(c,"og:title")
                description = getmeta(c,"og:description")
                image = getmeta(c,'og:image') or getmeta(c,'og:image:url')

                items.append(dict(titre=getmeta(c,"og:title"),
                             link=link,
                             image=image,
                             description=getmeta(c,"og:description")))

        await client.logout()




    items = []
    try:
        client.loop.run_until_complete(client.start(discord_user.username,discord_user.password))
    except:
        client.loop.run_until_complete(client.logout())

    del cache[b'get_items']
    return items

if __name__ == "__main__":
    app.run()
