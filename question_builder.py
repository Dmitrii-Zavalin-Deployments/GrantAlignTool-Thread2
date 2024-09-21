import re

def split_into_chunks(text, max_chars=5000):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def build_questions(project_text, data):
    chunks = split_into_chunks(data)
    questions = []

    for chunk in chunks:
        questions.extend([
            f"How does the project \"{project_text}\" meet the grant requirements \"{chunk}\"? Explain your decision.",
            f"What aspects of the project \"{project_text}\" fulfill the grant requirements \"{chunk}\"?",
            f"What aspects of the project \"{project_text}\" fail to meet the grant requirements \"{chunk}\"?",
            f"How well does the project \"{project_text}\" match the grant requirements \"{chunk}\" overall?",
            f"What percentage does the project \"{project_text}\" meet the grant requirements \"{chunk}\"?",
            f"What should be added to the project \"{project_text}\" to maximize its match with the grant requirements \"{chunk}\" without making major changes? Provide the updated project description.",
            f"What is the percentage of match of the updated project description with the grant requirements \"{chunk}\"?",
            f"What are the risky points in these grant requirements: \"{chunk}\"?"
        ])
    
    return questions