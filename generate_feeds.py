import requests
from bs4 import BeautifulSoup
import feedgenerator
import datetime
import os
import re
import time
from urllib.parse import quote

# List of your favorite tags with their URLs and AO3 tag IDs
favorite_tags = [
    {"name": "Batfamily Members & Bruce Wayne", "url": "https://archiveofourown.org/tags/Batfamily%20Members%20*a*%20Bruce%20Wayne/works", "has_rss": False, "tag_id": None},
    {"name": "Clark Kent/Bruce Wayne", "url": "https://archiveofourown.org/tags/Clark%20Kent*s*Bruce%20Wayne/works", "has_rss": True, "tag_id": "6624"},
    {"name": "Derek Hale/Stiles Stilinski", "url": "https://archiveofourown.org/tags/Derek%20Hale*s*Stiles%20Stilinski/works", "has_rss": False, "tag_id": None},
    {"name": "Dick Grayson/Jason Todd", "url": "https://archiveofourown.org/tags/Dick%20Grayson*s*Jason%20Todd/works", "has_rss": False, "tag_id": None},
    {"name": "Dom Bang Chan (Stray Kids)", "url": "https://archiveofourown.org/tags/Dom%20Bang%20Chan%20(Stray%20Kids)/works", "has_rss": False, "tag_id": None},
    {"name": "Evan \"Buck\" Buckley/Eddie Diaz (9-1-1 TV)", "url": "https://archiveofourown.org/tags/Evan%20%22Buck%22%20Buckley*s*Eddie%20Diaz%20(9-1-1%20TV)/works", "has_rss": False, "tag_id": None},
    {"name": "Hal Jordan (Green Lantern)/Bruce Wayne", "url": "https://archiveofourown.org/tags/Hal%20Jordan%20(Green%20Lantern)*s*Bruce%20Wayne/works", "has_rss": False, "tag_id": None},
    {"name": "Jason Todd/Reader", "url": "https://archiveofourown.org/tags/Jason%20Todd*s*Reader/works", "has_rss": False, "tag_id": None},
    {"name": "Marinette Dupain-Cheng | Ladybug/Damian Wayne", "url": "https://archiveofourown.org/tags/Marinette%20Dupain-Cheng%20%7C%20Ladybug*s*Damian%20Wayne/works", "has_rss": False, "tag_id": None},
    {"name": "Merlin/Arthur Pendragon (Merlin)", "url": "https://archiveofourown.org/tags/Merlin*s*Arthur%20Pendragon%20(Merlin)/works", "has_rss": False, "tag_id": None},
    {"name": "Pack Alpha Derek Hale", "url": "https://archiveofourown.org/tags/Pack%20Alpha%20Derek%20Hale/works", "has_rss": False, "tag_id": None},
    {"name": "Tim Drake/Damian Wayne", "url": "https://archiveofourown.org/tags/Tim%20Drake*s*Damian%20Wayne/works", "has_rss": False, "tag_id": None},
    {"name": "Trans Tim Drake (DCU)", "url": "https://archiveofourown.org/tags/Trans%20Tim%20Drake%20(DCU)/works", "has_rss": False, "tag_id": None},
]

# Excluded tag IDs (Alpha/Beta/Omega Dynamics)
excluded_tag_ids = ['272593']

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
    
    # Sort by most recent updates
    url += "?work_search%5Bsort_column%5D=revised_at&work_search%5Bsort_direction%5D=desc"
    
    # Filter for English works only
    url += "&work_search%5Blanguage_id%5D=en"
    
    # Add filter to exclude ABO by tag ID (more reliable)
    for tag_id in excluded_tag_ids:
        url += f"&exclude_work_search%5Bfreeform_ids%5D%5B%5D={tag_id}"
    
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
        
        for work in works[:50]:  # Get the latest 50 works
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
            
            # Get rating
            rating_element = work.select_one('span.rating')
            rating = rating_element.text.strip() if rating_element else "Unknown Rating"
            
            # Get language, word count, chapters, and kudos
            stats = {}
            
            # Get language (should be English as per filter)
            language_element = work.select_one('dl.stats dd.language')
            language = language_element.text.strip() if language_element else "English"
            stats["Language"] = language
            
            # Get word count
            words_element = work.select_one('dl.stats dd.words')
            words = words_element.text.strip() if words_element else "Unknown"
            stats["Words"] = words
            
            # Get chapters
            chapters_element = work.select_one('dl.stats dd.chapters')
            chapters = chapters_element.text.strip() if chapters_element else "?"
            stats["Chapters"] = chapters
            
            # Get kudos
            kudos_element = work.select_one('dl.stats dd.kudos')
            kudos = kudos_element.text.strip() if kudos_element else "0"
            stats["Kudos"] = kudos
            
            # Get additional info (tags)
            meta_elements = work.select('ul.tags li')
            meta_content = ""
            for meta in meta_elements:
                meta_content += f"<li>{meta.text.strip()}</li>"
            
            # Create a stats table
            stats_html = "<table style='width:100%; margin-top:10px; margin-bottom:10px; border:1px solid #ddd;'><tr>"
            stats_html += f"<td><strong>Rating:</strong> {rating}</td>"
            for key, value in stats.items():
                stats_html += f"<td><strong>{key}:</strong> {value}</td>"
            stats_html += "</tr></table>"
            
            content = f"<p><strong>Author:</strong> {author}</p>{stats_html}<p><strong>Summary:</strong> {summary}</p><ul>{meta_content}</ul>"
            
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

def get_feed_url_with_params(tag_id):
    """Create a properly filtered URL for AO3 native feeds"""
    base_url = f"https://archiveofourown.org/tags/{tag_id}/feed.atom"
    # Add parameters to match our filtering
    params = "?language_id=en"
    # Add ABO exclusion
    for tag_id in excluded_tag_ids:
        params += f"&exclude_work_search[freeform_ids][]={tag_id}"
    
    return base_url + params

def get_rss_url(tag_info):
    """Get the RSS URL for a tag, either from AO3 or our generated feed"""
    if tag_info["has_rss"] and tag_info["tag_id"]:
        # Use the direct AO3 feed URL with tag ID and filtering params
        return get_feed_url_with_params(tag_info["tag_id"])
    
    # For tags without RSS or tag ID, use our generated feed
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
    # Create RSS feeds for tags that don't have RSS support
    for tag in favorite_tags:
        if not tag["has_rss"] or not tag["tag_id"]:
            print(f"Creating RSS feed for {tag['name']}...")
            create_rss_for_tag(tag)
            time.sleep(3)  # Be nice to AO3's servers
    
    # Create main HTML page
    create_main_page()
    print("Done! All feeds generated.")

if __name__ == "__main__":
    main()
