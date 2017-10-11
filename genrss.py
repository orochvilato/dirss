# -*- coding: utf-8 -*-
import discord_user
import discord
import asyncio
import re
import requests
import email.utils
import html
from string import Template
import jinja2
import os
channels = {'actualites.xml':{'id':'256392899720249344','label':'Actualités'},
            'reseaux_sociaux.xml':{'id':'293416436620197889','label':'Réseaux sociaux'}}


rss_length=15


client = discord.Client()
from jinja2 import Environment, PackageLoader, select_autoescape,FileSystemLoader
env = Environment(
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['html', 'xml'])
)



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

    for flux in channels.keys():
        channel = client.get_channel(channels[flux]['id'])
        items = []
        async for msg in client.logs_from(channel,limit=rss_length):
            links = re.search(r'(https?:[^ \n><]+)',msg.content)

            if links:
                for link in links.groups():
                    r = requests.get(link)
                    try:
                        c = r.content.decode('utf8')
                    except:
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

        with open('html/%s' % flux,'wb') as f:
            f.write(env.get_template('rss.html').render(items=items,
                                                        link="https://discordapp.com/channels/254215611264008192/"+channels[flux]['id'],
                                                        label=channels[flux]['label']
                                                        ).encode('utf8'))


    await client.logout()


try:
    client.loop.run_until_complete(client.start(discord_user.username,discord_user.password))
except:
    client.loop.run_until_complete(client.logout())
