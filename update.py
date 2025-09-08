import os
import re
from datetime import datetime

def get_language_info_from_path(path_parts):
    """Extract language and media information from path parts"""
    if len(path_parts) >= 2:
        # Format: news/{language_code}/{media_name}/...
        if path_parts[0] == 'news' and len(path_parts) >= 3:
            lang_code = path_parts[1].upper()
            media_name = path_parts[2].upper()
            return lang_code, media_name
        # Format: {language_code}/{media_name}/...
        elif len(path_parts) >= 2:
            lang_code = path_parts[0].upper()
            media_name = path_parts[1].upper()
            return lang_code, media_name
    
    return None, None

def get_project_structure():
    """Traverse the project directory and get the structure of news articles"""
    structure = {}
    
    # Walk through the directory
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        if root == '.':
            continue
            
        # Get relative path and split into parts
        rel_path = os.path.relpath(root, '.')
        path_parts = rel_path.split(os.sep)
        
        # Extract language and media info from path
        lang_code, media_name = get_language_info_from_path(path_parts)
        
        # Process markdown files
        md_files = [f for f in files if f.endswith('.md') and f != 'README.md']
        if md_files and lang_code:
            folder_key = f"{lang_code}_{media_name}" if media_name else lang_code
            if folder_key not in structure:
                structure[folder_key] = {
                    'language_code': lang_code,
                    'media_name': media_name,
                    'folder_path': rel_path,
                    'articles': []
                }
            
            for md_file in md_files:
                file_path = os.path.join(root, md_file)
                try:
                    # Extract title and date from markdown file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract title (first line starting with #)
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    title = title_match.group(1) if title_match else md_file.replace('.md', '')
                    
                    # Extract date from filename (YYYYMMDD format)
                    date_match = re.search(r'(\d{8})', md_file)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            date_obj = datetime.strptime(date_str, '%Y%m%d')
                            date_formatted = date_obj.strftime('%Y-%m-%d')
                        except:
                            date_formatted = date_str
                    else:
                        # Use file modification time
                        mtime = os.path.getmtime(file_path)
                        date_formatted = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                    
                    # Extract summary (first paragraph after title)
                    summary_match = re.search(r'\n\n([^\n]+)', content)
                    summary = summary_match.group(1) if summary_match else ''
                    if len(summary) > 150:
                        summary = summary[:150] + '...'
                    
                    structure[folder_key]['articles'].append({
                        'filename': md_file,
                        'title': title,
                        'date': date_formatted,
                        'summary': summary,
                        'filepath': file_path
                    })
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
    
    return structure

def get_existing_languages(structure):
    """Get list of existing languages from the structure"""
    languages = set()
    for folder_data in structure.values():
        languages.add(folder_data['language_code'])
    return sorted(list(languages))

def generate_language_showcase_html(languages):
    """Generate HTML for language showcase section"""
    if not languages:
        return ""
    
    language_html = []
    for lang in languages:
        language_html.append(f'<span class="language">{lang}</span>')
    
    languages_joined = "\n                ".join(language_html)
    return f'''
            <div class="language-showcase">
                {languages_joined}
            </div>'''

def generate_news_list_html(structure):
    """Generate HTML for news list based on project structure"""
    items_html = []
    
    # Sort folders by key for consistent ordering
    sorted_folders = sorted(structure.keys())
    
    for folder_key in sorted_folders:
        folder_data = structure[folder_key]
        language_code = folder_data['language_code']
        media_name = folder_data['media_name']
        articles = folder_data['articles']
        
        # Create language tag combining language code and media name
        language_tag = f"{language_code}"
        if media_name:
            language_tag += f" - {media_name}"
        
        # Sort articles by date (newest first)
        articles.sort(key=lambda x: x['date'], reverse=True)
        
        for article in articles:
            # Create relative path to the markdown file without .md extension
            relative_path = article['filepath'].replace('.md', '')
            
            item_html = f'''
            <li class="news-item">
                <div class="news-header">
                    <span class="news-date">{article['date']}</span>
                    <span class="language-tag">{language_tag}</span>
                    <a href="{relative_path}" class="news-title">{article['title']}</a>
                </div>
            </li>'''
            items_html.append(item_html)
    
    return '\n'.join(items_html)

def update_index_html():
    """Update index.html based on project structure and template"""
    try:
        # Get project structure
        structure = get_project_structure()
        
        if not structure:
            print("No articles found in the project structure")
            return False
        
        # Generate HTML components
        news_list_html = generate_news_list_html(structure)
        existing_languages = get_existing_languages(structure)
        language_showcase_html = generate_language_showcase_html(existing_languages)
        
        # Read template
        with open('index_template.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace language showcase section
        updated_content = re.sub(
            r'(<div class="language-showcase"\s*\>\s*).*?(\s*</div\s*\>)',
            f'\\1{language_showcase_html}\\2' if language_showcase_html else '',
            template_content,
            flags=re.DOTALL
        )
        
        # Replace news-list section
        updated_content = re.sub(
            r'(<ul class="news-list"\s*\>\s*).*?(\s*</ul\s*\>)',
            f'\\1{news_list_html}\\2',
            updated_content,
            flags=re.DOTALL
        )
        
        # Write to index.html
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Successfully updated index.html with {len(structure)} folders and {sum(len(data['articles']) for data in structure.values())} articles")
        return True
        
    except Exception as e:
        print(f"Error updating index.html: {e}")
        return False

if __name__ == '__main__':
    update_index_html()