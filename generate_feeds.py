import requests
from bs4 import BeautifulSoup
import feedgenerator
import datetime
import os
import re
import time
from urllib.parse import quote, urlencode

# List of your favorite tags with their URLs and AO3 tag IDs
favorite_tags = [
    {"name": "Batfamily Members & Bruce Wayne", "url": "https://archiveofourown.org/tags/Batfamily%20Members%20*a*%20Bruce%20Wayne/works", "has_rss": True, "tag_id": "35623937"},
    {"name": "Clark Kent/Bruce Wayne", "url": "https://archiveofourown.org/tags/Clark%20Kent*s*Bruce%20Wayne/works", "has_rss": True, "tag_id": "6624"},
    {"name": "Derek Hale/Stiles Stilinski", "url": "https://archiveofourown.org/tags/Derek%20Hale*s*Stiles%20Stilinski/works", "has_rss": True, "tag_id": "264659"},
    {"name": "Dick Grayson/Jason Todd", "url": "https://archiveofourown.org/tags/Dick%20Grayson*s*Jason%20Todd/works", "has_rss": True, "tag_id": "41277"},
    {"name": "Dom Bang Chan (Stray Kids)", "url": "https://archiveofourown.org/tags/Dom%20Bang%20Chan%20(Stray%20Kids)/works", "has_rss": True, "tag_id": "74402449"},
    {"name": "Evan \"Buck\" Buckley/Eddie Diaz (9-1-1 TV)", "url": "https://archiveofourown.org/tags/Evan%20%22Buck%22%20Buckley*s*Eddie%20Diaz%20(9-1-1%20TV)/works", "has_rss": True, "tag_id": "37467886"},
    {"name": "Hal Jordan (Green Lantern)/Bruce Wayne", "url": "https://archiveofourown.org/tags/Hal%20Jordan%20(Green%20Lantern)*s*Bruce%20Wayne/works", "has_rss": True, "tag_id": "57586766"},
    {"name": "Jason Todd/Reader", "url": "https://archiveofourown.org/tags/Jason%20Todd*s*Reader/works", "has_rss": True, "tag_id": "1764193"},
    {"name": "Marinette Dupain-Cheng | Ladybug/Damian Wayne", "url": "https://archiveofourown.org/tags/Marinette%20Dupain-Cheng%20%7C%20Ladybug*s*Damian%20Wayne/works", "has_rss": True, "tag_id": "33566737"},
    {"name": "Merlin/Arthur Pendragon (Merlin)", "url": "https://archiveofourown.org/tags/Merlin*s*Arthur%20Pendragon%20(Merlin)/works", "has_rss": True, "tag_id": "260746"},
    {"name": "Tim Drake/Damian Wayne", "url": "https://archiveofourown.org/tags/Tim%20Drake*s*Damian%20Wayne/works", "has_rss": True, "tag_id": "51673"},
    {"name": "Robincest", "url": "https://archiveofourown.org/tags/Robincest/works", "has_rss": True, "tag_id": "1407900"},
    {"name": "Robinpile", "url": "https://archiveofourown.org/tags/robinpile/works", "has_rss": True, "tag_id": "2474063"},
    {"name": "Trans Tim Drake (DCU)", "url": "https://archiveofourown.org/tags/Trans%20Tim%20Drake%20(DCU)/works", "has_rss": True, "tag_id": "54440642"},
]

# Common filter parameters
common_params = {
    "work_search[language_id]": "en",                      # English only
    "work_search[sort_column]": "revised_at",              # Sort by date updated
    "work_search[sort_direction]": "desc",                 # Most recent first
    "exclude_work_search[freeform_ids][]": "272593"        # Exclude Alpha/Beta/Omega Dynamics
}

# Headers to mimic a browser request and avoid caching
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

def get_filtered_ao3_feed_url(tag_id):
    """Create a filtered AO3 feed URL with the appropriate parameters"""
    base_url = f"https://archiveofourown.org/tags/{tag_id}/feed.atom"
    
    # Format the parameters for the URL, removing sort-related params
    # as these don't work in feed URLs the same way
    feed_params = common_params.copy()
    
    # Remove sort params as they don't apply to feeds
    feed_params.pop("work_search[sort_column]", None)
    feed_params.pop("work_search[sort_direction]", None)
    
    # Convert to query string
    params_str = urlencode(feed_params)
    if params_str:
        return f"{base_url}?{params_str}"
    else:
        return base_url

def get_rss_url(tag_info):
    """Get the RSS URL for a tag"""
    if tag_info["has_rss"] and tag_info["tag_id"]:
        # Use the direct AO3 feed URL with tag ID and filtering params
        return get_filtered_ao3_feed_url(tag_info["tag_id"])
    
    # Fallback: use our generated feed
    safe_tag_name = re.sub(r'[^\w\s]', '', tag_info["name"]).replace(' ', '_').lower()
    return f"https://mor-lays.github.io/ao3favtags/feeds/{safe_tag_name}.xml"

def create_main_page():
    """Create a main HTML page listing all feeds"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>AO3 Favorite Tags Feeds</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #990000; }
        ul { list-style-type: none; padding: 0; }
        li { margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        a { color: #990000; text-decoration: none; }
        .feed-url { font-size: 0.8em; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>AO3 Favorite Tags RSS Feeds</h1>
    <p>Add these feeds to your favorite RSS reader to stay updated with new works.</p>
    <p>Filters applied: English works only, No Alpha/Beta/Omega Dynamics, Sorted by most recent updates</p>
    <ul>
"""
    
    for tag in favorite_tags:
        rss_url = get_rss_url(tag)
        # Add a timestamp parameter to prevent caching
        timestamp = int(datetime.datetime.now().timestamp())
        rss_url_with_timestamp = f"{rss_url}{('&' if '?' in rss_url else '?')}t={timestamp}"
        html_content += f"""        <li>
            <strong><a href="{tag['url']}" target="_blank">{tag['name']}</a></strong>
            <div class="feed-url">Feed URL: <a href="{rss_url}" target="_blank">{rss_url}</a></div>
        </li>\n"""
    
    html_content += """    </ul>
    <p><small>Last updated: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</small></p>
</body>
</html>"""

    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

def main():
    # Create main HTML page with feed links
    create_main_page()
    print("Done! Index page with feed links generated.")
    print("Since all tags have RSS feeds, no custom feeds need to be generated.")

if __name__ == "__main__":
    main()
