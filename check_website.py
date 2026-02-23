import os

# Check website directory
website_path = '/home/dong/mytool/codeAnalysis/website'
print('Website directory exists:', os.path.exists(website_path))

if os.path.exists(website_path):
    print('Website contents:', os.listdir(website_path))
    
    # Check docs directory
    docs_path = os.path.join(website_path, 'docs')
    print('Docs directory exists:', os.path.exists(docs_path))
    
    if os.path.exists(docs_path):
        print('Docs contents:', os.listdir(docs_path))
        
        # Check modules directory
        modules_path = os.path.join(docs_path, 'modules')
        print('Modules directory exists:', os.path.exists(modules_path))
        
        if os.path.exists(modules_path):
            print('Modules contents:', os.listdir(modules_path))
            
            # Check if any module files exist
            module_files = [f for f in os.listdir(modules_path) if f.endswith('.md')]
            print('Module files found:', len(module_files))
            for file in module_files[:5]:  # Show first 5 files
                print(f'  - {file}')
            if len(module_files) > 5:
                print(f'  ... and {len(module_files) - 5} more files')

# Check index.md
index_path = os.path.join(website_path, 'index.md')
print('Index.md exists:', os.path.exists(index_path))

# Check vite.config.js
config_path = os.path.join(website_path, 'vite.config.js')
print('Vite.config.js exists:', os.path.exists(config_path))

# Check package.json
package_path = os.path.join(website_path, 'package.json')
print('Package.json exists:', os.path.exists(package_path))
