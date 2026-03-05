import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException

from llm_helper import llm

def process_posts(raw_file_path, processed_file_path="data/processed_posts.json"):
    enriched_posts = []
    with open(raw_file_path, encoding="utf-8") as file:
        posts = json.load(file)
        for post in posts:
            # print(post, "\n")
            metadata = extract_metadata(post)
            post_with_matadata = post | metadata
            enriched_posts.append(post_with_matadata)
    unified_tags = get_unified_tags(enriched_posts)

    for post in enriched_posts:
        current_tags = post['tags']
        new_tags = {unified_tags[tag] for tag in current_tags}
        post['tags'] = list(new_tags)
    
    with open(processed_file_path, encoding="utf-8", mode="w") as outfile:
        json.dump(enriched_posts, outfile, indent=4)

    for epost in enriched_posts:
        print(epost, "\n")

def get_unified_tags(posts_with_matadata):
    unique_tags = set()
    for post in posts_with_matadata:
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
    test_utl = str(unique_tags_list)
    response = chain.invoke(input={'tags': str(unique_tags_list)})

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to parse jobs.")
    
    return res

def extract_metadata(post):
    template = '''
    You are given a LinkedIn post. You need to extract number of lines, language of post and tags.
    1. Return a valid JSON. No preamble.
    2. JSON object should only have three keys: line_count, language and tags.
    3. tags is an array of text tags. Extract maximum two tags.
    4. Language should be English or Hinglish (Hinglish means Hini + English)

    Here's the post on which you need to perform this task:
    {post}
    '''
    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={'post': post})

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to parse jobs.")

    return res

if __name__ == "__main__":
    process_posts("data/raw_posts.json")