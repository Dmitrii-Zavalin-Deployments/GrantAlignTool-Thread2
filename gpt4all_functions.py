from gpt4all import GPT4All

# Initialize the GPT-4All model with a valid model name
model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")

# Function to ask questions
def ask_question(question, log_file):
    prompt = f"{question}\nAnswer:"
    response = model.generate(prompt, max_tokens=250)  # Set max_tokens to 250
    prompt_token_count = len(prompt.split())
    response_token_count = len(response.split())
    total_token_count = prompt_token_count + response_token_count
    log_file.write(f"Prompt tokens: {prompt_token_count}\n")  # Log the number of tokens in the prompt
    log_file.write(f"Response tokens: {response_token_count}\n")  # Log the number of tokens in the response
    log_file.write(f"Total tokens: {total_token_count}\n")  # Log the total number of tokens
    print(f"Prompt tokens: {prompt_token_count}")  # Print the number of tokens in the prompt
    print(f"Response tokens: {response_token_count}")  # Print the number of tokens in the response
    print(f"Total tokens: {total_token_count}")  # Print the total number of tokens
    return response.strip()

# Function to run GPT-4
def run_gpt4all(question, log_file):
    answer = ask_question(question, log_file)
    return answer