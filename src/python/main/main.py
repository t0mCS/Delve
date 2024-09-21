import json
import os
import requests

# Load the input JSON file
with open('/Users/jordanwhite/Library/Application Support/Electron/surfer_data/X Corp/Twitter Posts/twitter-001/twitter-001.json', 'r') as file:
    data = json.load(file)

tweets = data['content']  # The 'content' key contains the list of tweets

# Claude API endpoint and headers
CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'  # Example Claude API URL
API_KEY = ''  # Replace with your actual Claude API key
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    'anthropic-version': '2023-06-01'  # Replace with the correct version
}

def generate_replies(prompt):
    """Calls Claude API to generate replies based on the prompt."""
    payload = {
        'model': 'claude-3-5-sonnet-20240620',
        'max_tokens': 1024,
        'messages': [
            {
                'role': 'user',
                'content': f"{prompt}\n\nPlease provide 3 distinct reply suggestions, each on a new line."
            }
        ]
    }
    response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        content = result.get('content', [])
        if content and isinstance(content[0], dict):
            text = content[0].get('text', '')
            # Split the text into lines and return up to 3 non-empty lines
            suggestions = [line.strip() for line in text.split('\n') if line.strip()]
            return suggestions[:3]
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return []

def present_options(options):
    """Present reply options to the user and allow them to choose one."""
    print("Please select a reply (enter the number), or press 0 to skip:")
    for idx, option in enumerate(options, 1):
        print(f"{idx}. {option}")  # Just print the index here for clarity
    choice = int(input("Your choice: "))
    if choice == 0:
        return None
    else:
        return options[choice - 1]  # Return the selected option without the number

# Process only the most recent tweet (the first one in the list)
if tweets:
    most_recent_tweet = tweets[0]
    original_text = most_recent_tweet['text']  # Extract the tweet text
    
    print(f"Original Tweet: {original_text}")
    
    # Create a prompt for the Claude API to generate a response
    prompt = f"Original Tweet: {original_text}\nDraft a polite and engaging response."
    suggestions = generate_replies(prompt)
    
    if suggestions:
        selected_reply = present_options(suggestions)
        
        if selected_reply:
            # Prepare the output data structure without the index
            output_data = {
                'original_tweet': original_text,
                'selected_response': selected_reply  # Only save the selected string
            }

            # Construct the path to the Documents directory for saving output
            documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            output_filename = os.path.join(documents_path, f"response_{most_recent_tweet['timestamp'].replace(':', '-')}.json")  # Ensure unique filenames
            with open(output_filename, 'w') as outfile:
                json.dump(output_data, outfile, indent=4)
            print(f"File saved successfully: {output_filename}")
        else:
            print("No reply selected.")
    else:
        print("No suggestions generated.")
else:
    print("No tweets found.")