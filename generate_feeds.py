import requests
from bs4 import BeautifulSoup
import feedgenerator
import datetime
import os
import re
import time
from urllib.parse import quote

# List of your favorite tags with their URLs
favorite_tags = [
    {"name": "Batfamily Members & Bruce Wayne", "url": "https://archiveofourown.org/tags/Batfamily%20Members%20*a*%20Bruce%20Wayne/works", "has_rss": False},
    {"name": "Clark Kent/Bruce Wayne", "url": "https://archiveofourown.org/tags/Clark%20Kent*s*Bruce%20Wayne/works", "has_rss": False},
    {"name": "Derek Hale/Stiles Stilinski", "url": "https://archiveofourown.org/tags/Derek%20Hale*s*Stiles%20Stilinski/works", "has_rss": False},
    {"name": "Dick Grayson/Jason Todd", "url": "https://archiveofourown.org/tags/Dick%20Grayson*s*Jason%20Todd/works", "has_rss": False},
    {"name": "Dom Bang Chan (Stray Kids)", "url": "https://archiveofourown.org/tags/Dom%20Bang%20Chan%20(Stray%20Kids)/works", "has_rss": False},
    {"name": "Evan \"Buck\" Buckley/Eddie Diaz (9-1-1 TV)", "url": "https://archiveofourown.org/tags/Evan%20%22Buck%22%20Buckley*s*Eddie%20Diaz%20(9-1-1%20TV)/works", "has_rss": False},
    {"name": "Hal Jordan (Green Lantern)/Bruce Wayne", "url": "https://archiveofourown.org/tags/Hal%20Jordan%20(Green%20Lantern)*s*Bruce%20Wayne/works", "has_rss": False},
    {"name": "Jason Todd/Reader", "url": "https://archiveofourown.org/tags/Jason%20Todd*s*Reader/works", "has_rss": False},
    {"name": "Marinette Dupain-Cheng | Ladybug/Damian Wayne", "url": "https://archiveofourown.org/tags/Marinette%20Dupain-Cheng%20%7C%20Ladybug*s*Damian%20Wayne/works", "has_rss": False},
    {"name": "Merlin/Arthur Pendragon (Merlin)", "url": "https://archiveofourown.org/tags/Merlin*s*Arthur%20Pendragon%20(Merlin)/works", "has_rss": False},
    {"name": "Pack Alpha Derek Hale", "url": "https://archiveofourown.org/tags/Pack%20Alpha%20Derek%20Hale/works", "has_rss": False},
    {"name": "Tim Drake/Damian Wayne", "url": "https://archiveofourown.org/tags/Tim%20Drake*s*Damian%20Wayne/works", "has_rss": False},
    {"name": "Trans Tim Drake (DCU)", "url": "https://archiveofourown.org/tags/Trans%20Tim%20Drake%20(DCU)/works", "has_rss": False},
]

# Excluded tags
excluded_tags = ['Alpha/Beta/Omega Dynamics']

# Headers to mimic a browser request and avoid caching
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

def create_rss_for_tag(tag_info):
    """Create an RSS feed for a tag that doesn't have one natively"""
    tag_name = tag_info["name"]
    
    # Start with a clean URL
    url = tag_info["url"]
    
    # Add explicit sorting by updated date (descending order)
    url += "?work_search%5Bsort_column%5D=revised_at&work_search%5Bsort_direction%5D=desc"
    
    # Filter out explicit works by including all other ratings
    # Rating IDs: 10=General, 11=Teen, 12=Mature, 9=Not Rated
    url += "&work_search%5Brating_ids%5D%5B%5D=10&work_search%5Brating_ids%5D%5B%5D=11&work_search%5Brating_ids%5D%5B%5D=12&work_search%5Brating_ids%5D%5B%5D=9"
    
    # Add filter to exclude Alpha/Beta/Omega Dynamics
    for excluded_tag in excluded_tags:
        url += f"&work_search%5Bexcluded_tag_names%5D={quote(excluded_tag)}"
    
    print(f"Fetching works from: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        works = soup.select('li.work.blurb.group')
        
        print(f"Found {len(works)} works for {tag_name}")
        
        if len(works) > 0:
            first_work = works[0]
            title_element = first_work.select_one('h4.heading a')
            title = title_element.text.strip() if title_element else "Untitled Work"
            date_element = first_work.select_one('p.datetime')
            date_str = date_element.text.strip() if date_element else "No date"
            print(f"Most recent work: {title} ({date_str})")
        
        # Create the feed
        feed = feedgenerator.Atom1Feed(
            title=f"AO3 - {tag_name}",
            link=url,
            description=f"Latest works for {tag_name} on Archive of Our Own",
            language="en"
        )
        
        for work in works[:20]:  # Get the latest 20 works
            title_element = work.select_one('h4.heading a')
            title = title_element.text.strip() if title_element else "Untitled Work"
            link = f"https://archiveofourown.org{title_element['href']}" if title_element else url
            
            # Get author
            author_element = work.select_one('a[rel="author"]')
            author = author_element.text if author_element else "Anonymous"
            
            # Get summary
            summary_element = work.select_one('blockquote.summary')
            summary = summary_element.text.strip() if summary_element else "No summary available"
            
            # Get date
            date_element = work.select_one('p.datetime')
            date_str = date_element.text.strip() if date_element else None
            if date_str:
                try:
                    date = datetime.datetime.strptime(date_str, '%d %b %Y')
                except ValueError:
                    date = datetime.datetime.now()
            else:
                date = datetime.datetime.now()
            
            # Get additional info
            meta_elements = work.select('ul.tags li')
            meta_content = ""
            for meta in meta_elements:
                meta_content += f"<li>{meta.text.strip()}</li>"
            
            content = f"<p><strong>Author:</strong> {author}</p><p><strong>Summary:</strong> {summary}</p><ul>{meta_content}</ul>"
            
            feed.add_item(
                title=title,
                link=link,
                description=content,
                author_name=author,
                pubdate=date
            )
        
        # Create feeds directory if it doesn't exist
        os.makedirs('docs/feeds', exist_ok=True)
        
        # Write the feed to file
        safe_tag_name = re.sub(r'[^\w\s]', '', tag_name).replace(' ', '_').lower()
        with open(f'docs/feeds/{safe_tag_name}.xml', 'w', encoding='utf-8') as file:
            feed.write(file, 'utf-8')
        
        return safe_tag_name
        
    except Exception as e:
        print(f"Error creating feed for {tag_name}: {e}")
        return None

def get_rss_url(tag_info):
    """Get the RSS URL for a tag, either from AO3 or our generated feed"""
    if tag_info["has_rss"]:
        # For native AO3 feeds, we need to correct the URL encoding
        tag_url = tag_info["url"]
        # Replace the works part with feed.atom
        feed_url = tag_url.replace("/works", "/feed.atom")
        # Return the corrected URL
        return feed_url
    
    # For tags without RSS, use our generated feed
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
    <p>Filters applied: No Explicit works, No Alpha/Beta/Omega Dynamics</p>
    <ul>
"""
    
    for tag in favorite_tags:
        rss_url = get_rss_url(tag)
        # Add a timestamp parameter to prevent caching
        timestamp = int(datetime.datetime.now().timestamp())
        rss_url_with_timestamp = f"{rss_url}?t={timestamp}"
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
    # Create RSS feeds for all tags
    for tag in favorite_tags:
        print(f"Creating RSS feed for {tag['name']}...")
        create_rss_for_tag(tag)
        time.sleep(3)  # Be nice to AO3's servers
    
    # Create main HTML page
    create_main_page()
    print("Done! All feeds generated.")

if __name__ == "__main__":
    main()
