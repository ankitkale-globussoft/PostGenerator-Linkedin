import json
import os
import re
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from llm_helper import llm

def clean_text(text):
    if not isinstance(text, str):
        return text
    # Remove surrogate pairs that cause encoding errors
    return re.sub(r'[\ud800-\udfff]', '', text)

def process_posts(raw_file_path, processed_folder="data/processed_posts"):
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    enriched_posts = []
    base_name = os.path.basename(raw_file_path)
    clean_name = base_name.replace("raw_", "")
    processed_file_path = os.path.join(processed_folder, clean_name)

    print(f"Loading raw posts from {raw_file_path} for processing...")
    
    with open(raw_file_path, encoding="utf-8") as file:
        posts = json.load(file)
        for post in posts:
            
            if 'text' in post:
                post['text'] = clean_text(post['text'])
            
            metadata = extract_metadata(post)
            enriched_post = {**post, **metadata}
            enriched_posts.append(enriched_post)
    
    print("Unifying tags...")
    unified_tags = get_unified_tags(enriched_posts)

    for post in enriched_posts:
        current_tags = post['tags']
        new_tags = {unified_tags[tag] for tag in current_tags if tag in unified_tags}
        post['tags'] = list(new_tags)
    
    with open(processed_file_path, encoding="utf-8", mode="w") as outfile:
        # Use ensure_ascii=False to support emojis correctly while avoiding surrogate errors
        json.dump(enriched_posts, outfile, indent=4, ensure_ascii=False)

    print(f"Successfully processed. Saved to {processed_file_path}")
    
    os.remove(raw_file_path)
    print(f"Deleted raw file: {raw_file_path}")
    return processed_file_path

def get_unified_tags(posts_with_metadata):
    unique_tags = set()
    for post in posts_with_metadata:
        unique_tags.update(post['tags'])
    unique_tags_list = ', '.join(unique_tags)

    template = '''
    I will give you list of tags, you need to unify tags with the following requirements,
    1. Tags are unified and merged to create a shorter list.
        Example 1: "Jobseekers", "Job Hunting" can be all merged into a single tag "Job Search".
        Example 2: "Motivation", "Inspirational", "Drive" can be mapped to "Motivation".
        Example 3" "Personal Growth", "Personal Development", "Self Improvement" can be mapped to "Self Improvement".
        Example 4" "Scam Alert", "Job Scam", etc. can be mapped to "Scams".  
    2. Each tag should follow title case convention. example: "Motivation", "Job Search".
    3. Output should be JSON object, No preamble
    4. Output should have mapping of original tag and the unified tag.
       For example: {{"Jobseekers": "Job Search", "Job Hunting": "Job Search", "Motivation": "Motivation"}}
    
    Here is the list of tags:
    {tags}
    '''
    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={'tags': str(unique_tags_list)})

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to parse tags.")
    
    return res

def extract_metadata(post):
    template = '''
    You are given a LinkedIn post. You need to extract number of lines, language of post and tags.
    1. Return a valid JSON. No preamble.
    2. JSON object should only have three keys: line_count, language and tags.
    3. tags is an array of text tags. Extract maximum two tags.
    4. Language should be English or Hinglish (Hinglish means Hindi + English)

    Here's the post on which you need to perform this task:
    {post}
    '''
    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={'post': str(post)})

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to extract metadata.")

    return res

if __name__ == "__main__":
    pass