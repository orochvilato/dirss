# -*- coding: utf-8 -*-
import discord_user
import discord
import asyncio
import re
import requests
import email.utils
import html
from string import Template
from flask import Flask,make_response, render_template
from diskcache import Cache
channels = {'actualites.xml':{'id':'256392899720249344','label':'Actualités'},
            'reseaux_sociaux.xml':{'id':'293416436620197889','label':'Réseaux sociaux'}}
cache = Cache('/tmp/rsscache')

rss_length=15

app = Flask(__name__)
client = discord.Client()

@app.route("/<flux>")
def getflux(flux):
    if flux=="fetch":
        for flux in channels.keys():
            print(flux)
            cache.set(flux,getItems(flux))

        return "OK",200

    if not flux in channels.keys():
        flux = list(channels.keys())[0]

    items = cache[flux]

    #items = "".join([item.substitute(it) for it in items])
    #rssflux = flux.substitute(items=items,link="https://discordapp.com/channels/254215611264008192/256392899720249344").encode('utf8')

    return render_template('rss.html',items=items,link="https://discordapp.com/channels/254215611264008192/"+channels[flux]['id'],label=channels[flux]['label']), 200, {'Content-Type': 'application/rss+xml; charset=utf-8'}


def getItems(flux):
    cache.set('get_'+flux,True,expire=180)
    client = discord.Client()

    def getmeta(t,property):
        import re
        g = re.search(r'<meta  {0,1}property="'+property+'"[^>]*content="([^"]+)"',t)
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


        channel = client.get_channel(channels[flux]['id'])

        async for msg in client.logs_from(channel,limit=rss_length):
            links = re.search(r'(https?:[^ \n><]+)',msg.content)

            if links:
                for link in links.groups():
                    r = requests.get(link)

                    c = r.content.decode(r.encoding)

                    site = getmeta(c,"og:site_name")
                    title = getmeta(c,"og:title")
                    description = getmeta(c,"og:description")

                    date = email.utils.format_datetime(msg.timestamp)
                    image = getmeta(c,'og:image') or getmeta(c,'og:image:url')

                    items.append(dict(titre=getmeta(c,"og:title"),
                             link=link,
                             date=date,
                             site=site,
                             image=image,
                             description=getmeta(c,"og:description")))


            await client.logout()




    items = []
    #try:
    client.loop.run_until_complete(client.start(discord_user.username,discord_user.password))
    #except:
    #client.loop.run_until_complete(client.logout())

    del cache['get_'+flux]
    return items

if __name__ == "__main__":
    app.run()
