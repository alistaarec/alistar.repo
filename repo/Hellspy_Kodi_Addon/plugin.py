import routing
import urllib.parse
import requests
from bs4 import BeautifulSoup
import subprocess
import platform
import os
import time
import xbmc
import xbmcgui
import xbmcplugin
import sys



plugin = routing.Plugin()
# Your TMDb API Key here
API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxx'

@plugin.route('/')
def home():
    # Create a Search Button
    list_item = xbmcgui.ListItem(label="Vyhledat filmy nebo serialy")
    url = plugin.url_for(search)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@plugin.route('/search')
def search():
    dialog = xbmcgui.Dialog()
    query = dialog.input("Zadej název titulu:")
    if not query:
        xbmcgui.Dialog().notification("Error", "Prazdne pole.", xbmcgui.NOTIFICATION_ERROR, 5000)
        return

    search_and_show_results(query)

def search_and_show_results(query):
    results = search_hellspy(query)

    if not results:
        xbmcgui.Dialog().notification("Nenalezeno", "Nic nebylo nalezeno.", xbmcgui.NOTIFICATION_INFO, 5000)
        return

    for idx, result in enumerate(results, 1):
        title = f"{result['title']} ({result['size']}, {result['duration']})"
        url = plugin.url_for(play_stream_from_search, link=result['url'])
        list_item = xbmcgui.ListItem(title)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@plugin.route('/play')
def play_from_tmdb():

    dialog = xbmcgui.Dialog()
    query = dialog.input("Zadej název titulu:")       

    results = search_hellspy(query)

    if not results:
        xbmcgui.Dialog().notification("Error", "No results found on Hellspy.", xbmcgui.NOTIFICATION_ERROR, 5000)
        return

    # Create a list of titles to show in Kodi Dialog
    options = [f"{res['title']} ({res['size']}, {res['duration']})" for res in results]

    # Show select dialog
    dialog = xbmcgui.Dialog()
    selected_index = dialog.select("Choose stream to play:", options)

    if selected_index == -1:
        xbmcgui.Dialog().notification("Canceled", "No stream selected.", xbmcgui.NOTIFICATION_INFO, 3000)
        return

    selected_result = results[selected_index]

    stream_url = get_stream_url(selected_result["url"])

    if stream_url:
        list_item = xbmcgui.ListItem(path=stream_url)
        list_item.setMimeType('video/mp4')
        list_item.setProperty('inputstream', 'inputstream.adaptive')
        list_item.setContentLookup(False)
        xbmc.Player().play(stream_url, list_item)
    else:
        xbmcgui.Dialog().notification("Error", "Stream not found.", xbmcgui.NOTIFICATION_ERROR, 5000)

@plugin.route('/play_stream_from_search/<path:link>')
def play_stream_from_search(link):
    stream_url = get_stream_url(link)
    if stream_url:
        list_item = xbmcgui.ListItem(path=stream_url)
        list_item.setMimeType('video/mp4')
        list_item.setProperty('inputstream', 'inputstream.adaptive')
        list_item.setContentLookup(False)
        xbmc.Player().play(stream_url, list_item)
    else:
        xbmcgui.Dialog().notification("Error", "Chyba pri prehravani streamu.", xbmcgui.NOTIFICATION_ERROR, 5000)


def search_tmdb(query, content_type='movie'):
    base_url = 'https://api.themoviedb.org/3/search/'
    url = f"{base_url}{content_type}"
    params = {
        'api_key': API_KEY,
        'query': query,
        'language': 'en-US',
        'page': 1
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        results = response.json().get('results', [])
        return results
    else:
        xbmcgui.Dialog().notification("Error", f"TMDb Error: {response.status_code}", xbmcgui.NOTIFICATION_ERROR, 5000)
        return []


def search_hellspy(query):
    url = f"https://hellspy.to/?query={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []

    for item in soup.select("a.result-video"):
        title_elem = item.select_one("h3")
        link = item.get("href")
        info = item.select("div.thumbnail-info p")  # Contains size and duration

        if title_elem and link:
            title = title_elem.text.strip()
            file_size = info[0].text.strip() if len(info) > 0 else "?"
            duration = info[1].text.strip() if len(info) > 1 else "?"
            results.append({
                "title": title,
                "url": link,
                "size": file_size,
                "duration": duration
            })

    return results


def get_stream_url(video_page_url):
    hlink = "https://hellspy.to"
    video_page_url = hlink + video_page_url
    print(video_page_url)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(video_page_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    video_tag = soup.find("a", {
    "class": "link-button button-xl"
})
    if video_tag:
        href = video_tag.get("href")
        download_name = video_tag.get("download")
        classes = video_tag.get("class")

        print("Download URL:", href)
        print("Download name:", download_name)
        print("Classes:", classes)
        return(href)
    else:
        xbmcgui.Dialog().notification("No link", "Nedostupny link.", xbmcgui.NOTIFICATION_INFO, 5000)
        return None


def hellspy_search(search_name):
    results = search_hellspy(search_name)

    if not results:
        xbmcgui.Dialog().notification("Nenalezeno", "Nic nebylo nalezeno.", xbmcgui.NOTIFICATION_INFO, 5000)
        exit()

    items = []
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['title']} ({result['size']}, {result['duration']})")

        items.append(f"{result['title']} ({result['size']}) ({result['duration']})")
    
    dialog = xbmcgui.Dialog()
    index = dialog.select("Select a file", items)

    if index != -1:
        selected = results[index]
        selected_name = selected.get('title')
        stream_url = get_stream_url(selected.get("url"))
        play_stream(stream_url)
    else:
        xbmcgui.Dialog().notification("Zruseno", "Vyber zrusen.", xbmcgui.NOTIFICATION_INFO, 3000)
     


def let_user_choose(results):
    """Show results and let user pick one."""
    if not results:
        xbmcgui.Dialog().notification("Nenalezeno", "Nic nebylo nalezeno.", xbmcgui.NOTIFICATION_INFO, 5000)
        return None

    items = []
    for idx, result in enumerate(results[:10]):  # Limit to top 10 results
        name = result.get('title') or result.get('name')
        year = (result.get('release_date') or result.get('first_air_date') or '')[:4]
        items.append(f"{name} ({year})")

    dialog = xbmcgui.Dialog()
    index = dialog.select("Select a movie/show", items)

    if index != -1:
        selected = results[index]
        selected_name = selected.get('title') or selected.get('name')
        return selected_name
    else:
        xbmcgui.Dialog().notification("Zruseno", "Vyber zrusen.", xbmcgui.NOTIFICATION_INFO, 3000)
        return None

"""def play_stream(stream_url):
    if stream_url:
        list_item = xbmcgui.ListItem(path=stream_url)
        list_item.setMimeType('video/mp4')
        list_item.setProperty('inputstream', 'inputstream.adaptive')  # Important for odd URLs
        list_item.setContentLookup(False)
        #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=list_item)
        xbmc.Player().play(stream_url, list_item)
    else:
        xbmcgui.Dialog().notification("Error", "Chyba pri prehravani streamu", xbmcgui.NOTIFICATION_ERROR, 5000)"""
 
def play_stream(stream_url):
    if stream_url:
        list_item = xbmcgui.ListItem(path=stream_url)
        list_item.setMimeType('video/mp4')
        list_item.setProperty('inputstream', 'inputstream.adaptive')
        list_item.setContentLookup(False)

        # Correct way for plugins
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)
    else:
        xbmcgui.Dialog().notification("Error", "Chyba pri prehravani streamu", xbmcgui.NOTIFICATION_ERROR, 5000)


if __name__ == '__main__':
    plugin.run()
