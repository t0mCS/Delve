import time
import os
from playwright.sync_api import sync_playwright, expect
import sys, multiprocessing
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QTextEdit, QSizePolicy, QPushButton)
from PyQt5.QtGui import QFont, QIcon, QCursor, QPixmap, QColor
from PyQt5.QtCore import Qt

class TweetFrame(QFrame):
    def __init__(self, text, is_original=False, parent=None):
        super().__init__(parent)
        self.setObjectName("tweetFrame")
        layout = QVBoxLayout()

        # Tweet text
        self.tweet_text = QLabel(text)
        self.tweet_text.setWordWrap(True)
        self.tweet_text.setStyleSheet(f"color: #000000; font-size: 16px;")

        layout.addWidget(self.tweet_text)

        self.setLayout(layout)
        self.setStyleSheet(f"""
            QFrame#tweetFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E1E8ED;
                border-radius: 12px;
                padding: 10px;
                margin-bottom: 10px;
            }}
        """)

class TweetResponder(QWidget):
    def __init__(self, original_post, reply):
        super().__init__()
        self.original_post = original_post
        self.reply = reply
        self.setWindowTitle("Tweet and Reply")
        self.resize(500, 400)
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F8FA;
                color: #14171A;
                font-family: "Helvetica Neue", Arial, sans-serif;
            }
            QLabel {
                color: #14171A;
            }
            QPushButton {
                background-color: #1DA1F2;
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1A91DA;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        # Original Tweet Display
        self.tweet_frame = TweetFrame(self.original_post, is_original=True)
        main_layout.addWidget(self.tweet_frame)

        # Reply Display
        if self.reply != "no replies":
            self.reply_frame = TweetFrame(self.reply)
            main_layout.addWidget(self.reply_frame)
        else:
            no_reply_label = QLabel("No replies yet")
            no_reply_label.setStyleSheet("color: #657786; font-style: italic;")
            main_layout.addWidget(no_reply_label)

        # Replies Buttons Layout
        self.buttons_layout = QVBoxLayout()
        main_layout.addLayout(self.buttons_layout)

        self.setLayout(main_layout)

        # Generate replies only if there's no existing reply
        if self.reply == "no replies":
            self.generate_replies()

    def load_tweet(self, reply):
        # This method is no longer needed as we're passing the data directly
        pass

    def generate_replies(self):
        if not self.original_post:
            QMessageBox.warning(self, "Warning", "No original tweet to reply to.")
            return

        # Create a prompt for the Claude API to generate a response
        prompt = f"Original Tweet: {self.original_post}\nHey Claude, can you reply to this comment in a way that sounds natural, as if a person were saying it casually over text? Show a bit of personality, but don't be overly formal or stiff. Keep it real. Don't be too enthusiastic or too negative. Just be chill and friendly."

        # Call the API to get replies
        suggestions = self.call_claude_api(prompt)

        if suggestions:
            # Clear any existing buttons
            for i in reversed(range(self.buttons_layout.count())):
                widget = self.buttons_layout.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)

            # Create buttons for each suggestion
            for suggestion in suggestions:
                reply_button = QPushButton(suggestion)
                reply_button.clicked.connect(lambda _, s=suggestion: self.save_reply(s))
                self.buttons_layout.addWidget(reply_button)

            # Add the "No Response" button
            no_response_button = QPushButton("No Response")
            no_response_button.clicked.connect(self.no_response)
            self.buttons_layout.addWidget(no_response_button)
        else:
            QMessageBox.information(self, "No Suggestions", "No suggestions generated.")

    def call_claude_api(self, prompt):
        CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'
        API_KEY = os.getenv('CLAUDE_API_KEY')
        if not API_KEY:
            QMessageBox.critical(self, "API Key Error", "Claude API key not found. Please set the CLAUDE_API_KEY environment variable.")
            return []

        headers = {
            'Content-Type': 'application/json',
            'x-api-key': API_KEY,
            'anthropic-version': '2023-06-01'
        }

        payload = {
            'model': 'claude-3-5-sonnet-20240620',
            'max_tokens': 1024,
            'messages': [
                {
                    'role': 'user',
                    'content': f"{prompt}\n\nPlease provide 3 distinct reply suggestions, each on a new line. Say nothing other than the suggestions, no intro to it or anything other than the 3 suggestions."
                }
            ]
        }

        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [])
            if content and isinstance(content[0], dict):
                text = content[0].get('text', '')
                suggestions = [line.strip() for line in text.split('\n') if line.strip()]
                return suggestions[:3]
        else:
            QMessageBox.critical(self, "API Error", f"Error: {response.status_code}, {response.text}")
        return []

    def save_reply(self, selected_reply):
        output_data = {
            'original_tweet': self.original_post,
            'selected_response': selected_reply
        }

        # Construct the path to the Documents directory for saving output
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        output_filename = os.path.join(documents_path, f"response_{self.tweet_timestamp.replace(':', '-')}.json")  # Ensure unique filenames
        try:
            with open(output_filename, 'w') as outfile:
                json.dump(output_data, outfile, indent=4)
            QMessageBox.information(self, "Success", f"Response saved successfully: {output_filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
        self.close()

    def no_response(self):
        QMessageBox.information(self, "No Response", "You have chosen not to respond.")
        self.close()

CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'  # Example Claude API URL
API_KEY = ''  # Replace with your actual Claude API key
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    'anthropic-version': '2023-06-01'  # Replace with the correct version
}

def generate_claude_replies(prompt):
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


# Replace these with your own X credentials
USERNAME = 'schtwiller'
PASSWORD = 'IlikeMLAI!'

def login_x(page):
    print("Navigating to login page...")
    page.goto("https://x.com/login", wait_until="networkidle")
    print("Page loaded.")

    # Wait for and fill in the username
    username_selector = 'input[name="text"]'
    print("Waiting for username input...")
    page.wait_for_selector(username_selector, state='visible', timeout=60000)
    print("Filling username...")
    page.fill(username_selector, USERNAME)

    # Press Enter instead of clicking "Next"
    print("Pressing Enter after username...")
    page.press(username_selector, 'Enter')

    # Wait for and fill in the password
    password_selector = 'input[name="password"]'
    print("Waiting for password input...")
    page.wait_for_selector(password_selector, state='visible', timeout=60000)
    print("Filling password...")
    page.fill(password_selector, PASSWORD)

    # Press Enter to log in instead of clicking the button
    print("Pressing Enter to log in...")
    page.press(password_selector, 'Enter')

    # Wait for navigation to complete
    print("Waiting for navigation to complete...")

    page.wait_for_timeout(5000)  # Additional wait to ensure everything is loaded

def get_most_recent_tweet_and_reply(page):
    print(f"Navigating to {USERNAME}'s profile...")
    page.goto(f"https://x.com/{USERNAME}")

    print("Scrolling to load more tweets...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)  # Wait for content to load

    print("Locating the most recent tweet...")
    tweet_selector = 'article[data-testid="tweet"]'
    page.wait_for_selector(tweet_selector)
    tweets = page.query_selector_all(tweet_selector)
    print(tweets if tweets else "NO TWEETS LOCATED BRUH")
    if tweets:
        most_recent_tweet = tweets[0]
        print("Clicking on the most recent tweet...")
        most_recent_tweet.click()

        page.wait_for_timeout(2000)  # Wait for content to load

        print("Extracting post URL...")
        post_url = page.url

        print("Extracting original post...")
        original_post = page.query_selector('div[data-testid="tweetText"]')
        original_post_text = original_post.inner_text() if original_post else "No original post found"

        print("Checking for replies...")
        replies = page.query_selector_all('div[data-testid="cellInnerDiv"] article')

        if len(replies) > 1:
            reply_text = replies[1].query_selector('div[data-testid="tweetText"]').inner_text()
            print("Reply found.")
        else:
            reply_text = "no replies"
            print("No replies found.")

        return post_url, original_post_text, reply_text
    else:
        print("No tweets found")
        return None, None, None

def save_to_file(content, filename):
    downloads_folder = os.path.expanduser("~/Downloads")
    file_path = os.path.join(downloads_folder, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Saved to {file_path}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        page.set_default_timeout(60000)  # Set default timeout to 60 seconds

        try:
            login_x(page)
            # Save a screenshot for debugging
            page.screenshot(path="after_login.png")

            # Retrieve most recent tweet URL, original post, and reply
            post_url, original_post, reply = get_most_recent_tweet_and_reply(page)

            if post_url and original_post:
                print(f"Most recent tweet URL: {post_url}")
                print(f"Original tweet: {original_post}")
                print(f"Reply: {reply}")

                prompt = f"Original Tweet: {original_post}\nDraft a polite and engaging unique and clever response."
                suggestions = generate_claude_replies(prompt)

                app = QApplication(sys.argv)
                window = TweetResponder(original_post, suggestions)
                window.show()
                sys.exit(app.exec_())
            else:
                print("Couldn't retrieve the tweet or URL.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # Save a screenshot when an error occurs
            page.screenshot(path="error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
