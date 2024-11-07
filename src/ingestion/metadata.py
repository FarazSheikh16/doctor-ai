import re

def extract_section_and_topic(text):
    section_pattern = r"(Section \d+ .+?)(?=\s+\d+\s+|\Z)"  
    topic_pattern = r"(\d+)\s+(.+)" 
    
    section_match = re.search(section_pattern, text)
    topic_match = re.search(topic_pattern, text)
    
    section_name = section_match.group(1) if section_match else None
    topic_name = topic_match.group(2) if topic_match else None
    
    return section_name, topic_name

def generate_metadata_chunks_with_section_and_topic(text_chunks):
    metadata_chunks = []
    
    for chunk in text_chunks:
        section_name, topic_name = extract_section_and_topic(chunk["content"])
        metadata_chunks.append({
            "page_num": chunk["page_num"],
            "content": chunk["content"],
            "section_name": section_name,
            "topic_name": topic_name
        })
    
    return metadata_chunks
