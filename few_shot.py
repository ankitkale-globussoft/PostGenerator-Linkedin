import json
import pandas as pd
import os
import re

class FewShotPosts:
    def __init__(self, processed_dir="data/processed_posts"):
        # Disable pyarrow string backend to prevent strict UTF-8 crashes with emojis
        pd.options.mode.string_storage = "python"
        self.df = None
        self.unique_tags = []
        self.load_posts(processed_dir)
    
    def clean_text(self, text):
        if not isinstance(text, str):
            return text
        # Remove surrogate pairs that cause encoding errors (\ud800-\udfff)
        return re.sub(r'[\ud800-\udfff]', '', text)

    def load_posts(self, directory):
        all_posts = []
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            self.df = pd.DataFrame()
            return

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, encoding="utf-8") as f:
                        posts = json.load(f)
                    
                    # Ensure it's a list
                    if not isinstance(posts, list):
                        posts = [posts]
                    
                    # Sanitization: Clean all strings in every post to remove surrogates
                    for post in posts:
                        for key, value in post.items():
                            if isinstance(value, str):
                                post[key] = self.clean_text(value)
                    
                    all_posts.extend(posts)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        if not all_posts:
            self.df = pd.DataFrame()
            self.unique_tags = []
            return

        # Create DataFrame
        self.df = pd.json_normalize(all_posts)
        
        # Categorize length based on line_count
        if 'line_count' in self.df.columns:
            self.df['length'] = self.df['line_count'].apply(self.categorize_length)
        else:
            self.df['length'] = "Medium"

        # Unique tags
        if 'tags' in self.df.columns:
            self.unique_tags = sorted(list(set(self.df['tags'].explode().dropna())))
        else:
            self.unique_tags = []

    def categorize_length(self, line_count):
        if line_count < 5:
            return "Short"
        elif 5 <= line_count <= 10:
            return "Medium"
        else:
            return "Long"
        
    def get_tags(self):
        return self.unique_tags
    
    def get_filtered_posts(self, length, language, tag):
        if self.df is None or self.df.empty:
            return []
            
        df_filtered = self.df[
            (self.df["language"] == language) &
            (self.df["length"] == length) &
            (self.df["tags"].apply(lambda tags: tag in tags if isinstance(tags, list) else False))
        ]
        return df_filtered.to_dict(orient="records")

if __name__ == "__main__":
    fs = FewShotPosts()
    print(fs.get_tags())
