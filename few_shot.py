import json
import pandas as pd
import re

class FewShotPosts:
    def __init__(self, file_path="data/processed_posts.json"):
        self.df = None
        self.unique_tags = None
        self.load_posts(file_path)
    
    def load_posts(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            posts = json.load(f)
        posts = json.loads(json.dumps(posts, ensure_ascii=False).encode("utf-8", "ignore").decode("utf-8"))
        
        self.df = pd.json_normalize(posts)
        self.df['length'] = self.df['line_count'].apply(self.categorize_length)
        all_tags = self.df['tags'].apply(lambda x: x).sum()
        self.unique_tags = list(set(all_tags))

    '''
    def load_posts(self, file_path):
    # Disable pyarrow string backend (prevents strict UTF-8 crash)
        pd.options.mode.string_storage = "python"

        def clean_text(text):
            if not isinstance(text, str):
                return text
            
            # Remove invalid surrogate pairs
            text = re.sub(r'[\ud800-\udfff]', '', text)

            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
            # Remove control characters (like \x08)

            return text

        with open(file_path, encoding="utf-8") as f:
            posts = json.load(f)

        # Clean all string fields in every post
        for post in posts:
            for key, value in post.items():
                if isinstance(value, str):
                    post[key] = clean_text(value)

        df = pd.json_normalize(posts)

        # Force normal Python object dtype (extra safety)
        df = df.astype(object)

        self.df = df
        self.df['length'] = self.df['line_count'].apply(self.categorize_length)
        self.unique_tags = df["tags"].explode().unique().tolist()
    '''

    def categorize_length(self, line_count):
        if line_count < 5:
            return "Short"
        elif 5 < line_count <= 10:
            return "Medium"
        else:
            return "Long"
        
    def get_tags(self):
        return self.unique_tags
    
    def get_filtered_posts(self, length, language, tag):
        df_filtered = self.df[
            (self.df["language"] == language) &
            (self.df["length"] == length) &
            (self.df["tags"].apply(lambda tags: tag in tags))
        ]
        return df_filtered.to_dict(orient="records")

if __name__ == "__main__":
    fs = FewShotPosts()
    posts = fs.get_filtered_posts("Long","English","Motivation")
    print(posts)
