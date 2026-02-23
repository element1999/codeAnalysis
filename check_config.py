import os

# Check website directory
website_path = '/home/dong/mytool/codeAnalysis/website'
print('Website directory exists:', os.path.exists(website_path))

if os.path.exists(website_path):
    print('Website contents:', os.listdir(website_path))
    
    # Check config file
    config_path = os.path.join(website_path, 'vite.config.js')
    print('Config file exists:', os.path.exists(config_path))
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            print('Config content:')
            print(f.read())
    
    # Check index.md
    index_path = os.path.join(website_path, 'index.md')
    print('Index.md exists:', os.path.exists(index_path))
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            print('Index.md content:')
            print(f.read())
