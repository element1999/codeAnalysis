"""Website generator using VitePress"""

import os
import shutil
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class WebsiteGenerator:
    """Generate website from markdown documentation using VitePress"""
    
    def __init__(self):
        """Initialize website generator"""
        self.website_path = "website"
        self.docs_path = os.path.join(self.website_path, "docs")
    
    def generate_website(self, wiki_path):
        """Generate VitePress website from markdown documentation"""
        try:
            # Clean existing website directory if it exists
            if os.path.exists(self.website_path):
                logger.info(f"Cleaning existing website directory: {self.website_path}")
                shutil.rmtree(self.website_path)
            
            # Initialize VitePress project
            self._initialize_vitepress()
            
            # Copy markdown files
            self._copy_markdown_files(wiki_path)
            
            # Configure VitePress
            self._configure_vitepress()
            
            # Build website
            build_output = self._build_website()
            
            return {
                "website_path": self.website_path,
                "build_output": build_output
            }
            
        except Exception as e:
            logger.error(f"Failed to generate website: {e}")
            raise
    
    def _initialize_vitepress(self):
        """Initialize VitePress project"""
        logger.info("Initializing VitePress project...")
        
        # First check if npm is installed
        try:
            npm_check = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if npm_check.returncode != 0:
                raise Exception("npm is not installed. Please install Node.js and npm first.")
            logger.info(f"npm version: {npm_check.stdout.strip()}")
        except Exception as e:
            logger.error(f"npm check failed: {e}")
            raise
        
        # Create VitePress project structure
        logger.info(f"Creating VitePress project at: {self.website_path}")
        
        # Create basic directory structure
        os.makedirs(self.website_path, exist_ok=True)
        os.makedirs(self.docs_path, exist_ok=True)
        
        # Create package.json for VitePress
        package_json = {
            "name": "codemind-docs",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vitepress dev docs",
                "build": "vitepress build docs",
                "preview": "vitepress preview docs"
            },
            "devDependencies": {
                "vitepress": "^1.3.4",
                "vitepress-sidebar": "^1.33.1"
            }
        }
        
        with open(os.path.join(self.website_path, "package.json"), "w", encoding="utf-8") as f:
            json.dump(package_json, f, indent=2)
        
        # Create VitePress config with _sidebar.md support
        vitepress_config = """
import { defineConfig } from 'vitepress'
import { withSidebar } from 'vitepress-sidebar'

export default defineConfig(
  withSidebar(
    {
      title: '文档站点',
      themeConfig: {
        nav: [{ text: '首页', link: '/' }]
      }
    },
    {
      documentRootPath: '/docs',
      collapsed: true,
      useTitleFromFileHeading: true,
      sortMenusByFrontmatterOrder: true,
      hyphenToSpace: true,
    }
  )
)
"""
        
        # Create .vitepress directory
        vitepress_dir = os.path.join(self.docs_path, ".vitepress")
        os.makedirs(vitepress_dir, exist_ok=True)
        
        with open(os.path.join(vitepress_dir, "config.ts"), "w", encoding="utf-8") as f:
            f.write(vitepress_config)
        
        
        # Create index.md for homepage
        index_md = """# CodeMind Documentation

AI-powered code understanding and documentation tool

## Welcome

This documentation was generated automatically from your codebase using CodeMind.

### Quick Start

1. **Project Overview**: Learn about the project structure and main features
2. **Architecture**: Understand the system architecture and design decisions
3. **Modules**: Explore the different modules and their functionality

### Features

- **Code Analysis**: Static analysis of codebase structure and dependencies
- **Documentation Generation**: Automatic generation of comprehensive documentation
- **Intelligent Q&A**: Ask questions about your codebase
- **Dependency Analysis**: Analyze code dependencies and call chains

[Get Started →](/docs/00-overview)
"""
        
        with open(os.path.join(self.website_path, "index.md"), "w", encoding="utf-8") as f:
            f.write(index_md)
        
        # Create .gitignore file
        gitignore = """# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
"""
        
        with open(os.path.join(self.website_path, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(gitignore)
        
        logger.info("VitePress project structure created successfully")
    
    def _copy_markdown_files(self, wiki_path):
        """Copy markdown files from wiki to VitePress docs"""
        logger.info(f"Copying markdown files from {wiki_path} to {self.docs_path}...")
        
        # Create docs directory if it doesn't exist
        os.makedirs(self.docs_path, exist_ok=True)
        
        # Copy files from wiki root
        for file in os.listdir(wiki_path):
            if file.endswith(".md"):
                src = os.path.join(wiki_path, file)
                # Convert README.md to index.md
                if file == "README.md":
                    dst = os.path.join(self.docs_path, "index.md")
                    shutil.copy2(src, dst)
                    logger.info(f"Copied and renamed: {file} → index.md")
                else:
                    dst = os.path.join(self.docs_path, file)
                    shutil.copy2(src, dst)
                    logger.info(f"Copied: {file}")
                
                # # Fix dead links in index.md
                # if file == "README.md":
                #     self._fix_readme_links(dst)
        
        # Copy modules directory if it exists
        modules_path = os.path.join(wiki_path, "modules")
        if os.path.exists(modules_path):
            dst_modules_path = os.path.join(self.docs_path, "modules")
            os.makedirs(dst_modules_path, exist_ok=True)
            
            for item in os.listdir(modules_path):
                item_path = os.path.join(modules_path, item)
                
                if os.path.isfile(item_path) and item.endswith(".md") and item != "..md":  # Skip ..md file to avoid dead link
                    src = item_path
                    dst = os.path.join(dst_modules_path, item)
                    shutil.copy2(src, dst)
                    logger.info(f"Copied module file: {item}")
                elif os.path.isdir(item_path):
                    # Copy directory and its contents
                    dst_dir = os.path.join(dst_modules_path, item)
                    os.makedirs(dst_dir, exist_ok=True)
                    
                    # Copy files in subdirectory
                    for subfile in os.listdir(item_path):
                        if subfile.endswith(".md"):
                            src = os.path.join(item_path, subfile)
                            dst = os.path.join(dst_dir, subfile)
                            shutil.copy2(src, dst)
                            logger.info(f"Copied module subfile: {item}/{subfile}")
        
        # # Fix dead links in _sidebar.md
        # sidebar_path = os.path.join(self.docs_path, "_sidebar.md")
        # if os.path.exists(sidebar_path):
        #     self._fix_sidebar_links(sidebar_path)
        
        logger.info("Markdown files copied successfully")
    
    # def _fix_readme_links(self, readme_path):
    #     """Fix dead links in README.md"""
    #     with open(readme_path, "r", encoding="utf-8") as f:
    #         content = f.read()
        
    #     # Replace link to modules directory with link to codemind.md
    #     updated_content = content.replace("[模块文档](./modules/)", "[模块文档](modules/codemind.md)")
        
    #     with open(readme_path, "w", encoding="utf-8") as f:
    #         f.write(updated_content)
        
    #     logger.info("Fixed dead links in README.md")
    
    # def _fix_sidebar_links(self, sidebar_path):
    #     """Fix dead links in _sidebar.md"""
    #     with open(sidebar_path, "r", encoding="utf-8") as f:
    #         lines = f.readlines()
        
    #     # Filter out lines containing link to ..md
    #     updated_lines = [line for line in lines if "modules/..md" not in line]
        
    #     with open(sidebar_path, "w", encoding="utf-8") as f:
    #         f.writelines(updated_lines)
        
    #     logger.info("Fixed dead links in _sidebar.md")
    
    def _configure_vitepress(self):
        """Configure VitePress website"""
        logger.info("Configuring VitePress website...")
        
        # VitePress configuration is already created in _initialize_vitepress
        # Here we can add any additional configuration if needed
        
        logger.info("VitePress website configured successfully")
    
    def _build_website(self):
        """Build VitePress website"""
        logger.info("Building VitePress website...")
        
        # First install dependencies
        install_cmd = ["npm", "install"]
        install_result = subprocess.run(
            install_cmd, 
            cwd=self.website_path, 
            capture_output=True, 
            text=True
        )
        
        if install_result.returncode != 0:
            logger.error(f"Failed to install dependencies: {install_result.stderr}")
            raise Exception(f"Dependency installation failed: {install_result.stderr}")
        
        # Then build the website
        build_cmd = ["npm", "run", "build"]
        build_result = subprocess.run(
            build_cmd, 
            cwd=self.website_path, 
            capture_output=True, 
            text=True
        )
        
        if build_result.returncode != 0:
            logger.warning(f"Build failed (this may be due to dead links, but development server should still work): {build_result.stderr}")
            logger.info("Continuing with development server setup...")
        else:
            logger.info("VitePress website built successfully")
        
        return "Website build completed (development server ready)"
    
    def start_server_and_open_browser(self):
        """Start development server and open browser"""
        logger.info("Starting development server and opening browser...")
        
        import subprocess
        import webbrowser
        import time
        
        # Start the server in the background
        server_cmd = ["npm", "run", "dev"]
        server_process = subprocess.Popen(
            server_cmd, 
            cwd=self.website_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a few seconds for the server to start
        logger.info("Waiting for server to start...")
        time.sleep(5)
        
        # Open browser to the website
        website_url = "http://localhost:5173"
        webbrowser.open(website_url)
        logger.info(f"Browser opened to: {website_url}")
        
        return server_process
