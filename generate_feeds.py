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
    {"name": "Batfamily Members & Bruce Wayne", "url": "https://archiveofourown.org/tags/Batfamily%20Members%20*a*%20Bruce%20Wayne/works", "tag_id": "35623937"},
    {"name": "Clark Kent/Bruce Wayne", "url": "https://archiveofourown.org/tags/Clark%20Kent*s*Bruce%20Wayne/works", "tag_id": "6624"},
    {"name": "Derek Hale/Stiles Stilinski", "url": "https://archiveofourown.org/tags/Derek%20Hale*s*Stiles%20Stilinski/works", "tag_id": "264659"},
    {"name": "Dick Grayson/Jason Todd", "url": "https://archiveofourown.org/tags/Dick%20Grayson*s*Jason%20Todd/works", "tag_id": "41277"},
    {"name": "Dom Bang Chan (Stray Kids)", "url": "https://archiveofourown.org/tags/Dom%20Bang%20Chan%20(Stray%20Kids)/works", "tag_id": "74402449"},
    {"name": "Evan \"Buck\" Buckley/Eddie Diaz (9-1-1 TV)", "url": "https://archiveofourown.org/tags/Evan%20%22Buck%22%20Buckley*s*Eddie%20Diaz%20(9-1-1%20TV)/works", "tag_id": "37467886"},
    {"name": "Hal Jordan (Green Lantern)/Bruce Wayne", "url": "https://archiveofourown.org/tags/Hal%20Jordan%20(Green%20Lantern)*s*Bruce%20Wayne/works", "tag_id": "57586766"},
    {"name": "Jason Todd/Reader", "url": "https://archiveofourown.org/tags/Jason%20Todd*s*Reader/works", "tag_id": "1764193"},
    {"name": "Marinette Dupain-Cheng | Ladybug/Damian Wayne", "url": "https://archiveofourown.org/tags/Marinette%20Dupain-Cheng%20%7C%20Ladybug*s*Damian%20Wayne/works", "tag_id": "33566737"},
    {"name": "Merlin/Arthur Pendragon (Merlin)", "url": "https://archiveofourown.org/tags/Merlin*s*Arthur%20Pendragon%20(Merlin)/works", "tag_id": "260746"},
    {"name": "Tim Drake/Damian Wayne", "url": "https://archiveofourown.org/tags/Tim%20Drake*s*Damian%20Wayne/works", "tag_id": "51673"},
    {"name": "Robincest", "url": "https://archiveofourown.org/tags/Robincest/works", "tag_id": "1407900"},
    {"name": "Robinpile", "url": "https://archiveofourown.org/tags/robinpile/works", "tag_id": "2474063"},
    {"name": "Trans Tim Drake (DCU)", "url": "https://archiveofourown.org/tags/Trans%20Tim%20Drake%20(DCU)/works", "tag_id": "54440642"},
    # New tags added
    {"name": "Tim Drake/Dick Grayson/Jason Todd/Damian Wayne", "url": "https://archiveofourown.org/tags/Tim%20Drake*s*Dick%20Grayson*s*Jason%20Todd*s*Damian%20Wayne/works", "tag_id": "394948"},
    {"name": "Stephanie Brown/Jason Todd", "url": "https://archiveofourown.org/tags/Stephanie%20Brown*s*Jason%20Todd/works", "tag_id": "79243"},
    {"name": "Damian Wayne/Reader", "url": "https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=Damian+Wayne%2FReader&tag_id=Damian+Wayne", "tag_id": "67567"},
    {"name": "Dick Grayson/Damian Wayne", "url": "https://archiveofourown.org/tags/Dick%20Grayson*s*Damian%20Wayne/works", "tag_id": "71872"},
]

# Headers to mimic a browser request and avoid caching
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

def create_filtered_url(tag_info):
    """Create a filtered URL for scraping from AO3"""
    base_url = tag_info["url"]
    
    # Check if URL already has parameters
    if '?' in base_url:
        # URL already has parameters, append our additional filters
        # First, keep the existing parameters and add our filters
        params = {
            "work_search[language_id]": "en",
            "exclude_work_search[freeform_ids][]": "272593",  # Exclude Alpha/Beta/Omega Dynamics
        }
        
        # Create a parameter string to append
        params_str = urlencode(params)
        return f"{base_url}&{params_str}"
    else:
        # URL has no parameters, add all our filters
        params = {
            "work_search[sort_column]": "revised_at",
            "work_search[sort_direction]": "desc",
            "work_search[language_id]": "en",
            "exclude_work_search[freeform_ids][]": "272593",  # Exclude Alpha/Beta/Omega Dynamics
            "commit": "Sort and Filter"
        }
        
        # Create a parameter string
        params_str = urlencode(params)
        return f"{base_url}?{params_str}"

def create_rss_for_tag(tag_info):
    """Create an RSS feed for a tag with proper filtering"""
    tag_name = tag_info["name"]
    
    # Create filtered URL for scraping
    url = create_filtered_url(tag_info)
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
            title=f"AO3 - {tag_name} (Filtered)",
            link=url,
            description=f"Latest works for {tag_name} on Archive of Our Own [English, No ABO]",
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

def get_rss_url(tag_info):
    """Get the RSS URL for a tag (our custom filtered feed)"""
    safe_tag_name = re.sub(r'[^\w\s]', '', tag_name).replace(' ', '_').lower()
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
        .disclaimer { font-size: 0.9em; margin-top: 20px; padding: 10px; background: #f9f9f9; border-left: 3px solid #990000; }
    </style>
</head>
<body>
    <h1>AO3 Favorite Tags RSS Feeds</h1>
    <p>Add these feeds to your favorite RSS reader to stay updated with new works.</p>
    <p><strong>Filters applied:</strong> English works only, No Alpha/Beta/Omega Dynamics, Sorted by most recent updates</p>
    <p><strong>Updates:</strong> Feeds refresh daily at 12:00 UTC</p>
    <ul>
"""
    
    for tag in favorite_tags:
        safe_tag_name = re.sub(r'[^\w\s]', '', tag["name"]).replace(' ', '_').lower()
        rss_url = f"https://mor-lays.github.io/ao3favtags/feeds/{safe_tag_name}.xml"
        html_content += f"""        <li>
            <strong><a href="{tag['url']}" target="_blank">{tag['name']}</a></strong>
            <div class="feed-url">Feed URL: <a href="{rss_url}" target="_blank">{rss_url}</a></div>
        </li>\n"""
    
    html_content += """    </ul>
    <div class="disclaimer">
        <p><strong>Note:</strong> These are custom-filtered feeds generated from AO3 content. They are updated daily and 
        contain the most recent 50 works from each tag, filtered to show English works only and exclude specific tags.</p>
    </div>
    <p><small>Last updated: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</small></p>
</body>
</html>"""

    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

def main():
    # Create custom RSS feeds for all tags
    for tag in favorite_tags:
        print(f"Creating filtered RSS feed for {tag['name']}...")
        create_rss_for_tag(tag)
        time.sleep(2)  # Be nice to AO3's servers
    
    # Create main HTML page
    create_main_page()
    print("Done! All filtered feeds generated.")

if __name__ == "__main__":
    main()
