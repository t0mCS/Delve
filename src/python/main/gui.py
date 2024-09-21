import sys
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QTextEdit, QSizePolicy)
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt

class TweetResponder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tweet Responder")
        self.resize(600, 700)
        self.setWindowIcon(QIcon('icon.png'))  # Optional: Set an application icon
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;  /* Black background */
                color: #FFFFFF;  /* White text */
                font-family: "Helvetica Neue", Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
            }
            QFrame {
                background-color: #1DA1F2;  /* X platform blue */
                color: #FFFFFF;
                border: 2px solid #1DA1F2;
                border-radius: 15px;
                padding: 5px;
            }
            QFrame:hover {
                background-color: #0d8ddb;
            }
            QTextEdit {
                background-color: #15202B;  /* Darker background for text area */
                color: #FFFFFF;
                border: none;
                padding: 5px;
                font-size: 16px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        # Set up the layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        # Original Tweet Label
        self.tweet_label = QLabel("Original Tweet:")
        self.tweet_label.setFont(QFont('Helvetica Neue', 16, QFont.Bold))
        main_layout.addWidget(self.tweet_label)

        # Original Tweet Display
        self.tweet_display = QTextEdit()
        self.tweet_display.setReadOnly(True)
        self.tweet_display.setFont(QFont('Helvetica Neue', 14))
        main_layout.addWidget(self.tweet_display)

        # Replies Buttons Layout
        self.buttons_layout = QVBoxLayout()
        main_layout.addLayout(self.buttons_layout)

        self.setLayout(main_layout)

        # Load the tweet data
        self.load_tweet()

        # Automatically generate replies
        self.generate_replies()

    def load_tweet(self):
        # Load the input JSON file
        try:
            with open('/Users/jordanwhite/Library/Application Support/Electron/surfer_data/X Corp/Twitter Posts/twitter-001/twitter-001.json', 'r') as file:
                data = json.load(file)
            tweets = data['content']  # The 'content' key contains the list of tweets
            if tweets:
                most_recent_tweet = tweets[0]
                self.original_text = most_recent_tweet['text']
                self.tweet_display.setPlainText(self.original_text)
                self.tweet_timestamp = most_recent_tweet['timestamp']
            else:
                self.tweet_display.setPlainText("No tweets found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load tweet data: {e}")

    def generate_replies(self):
        if not hasattr(self, 'original_text') or not self.original_text:
            QMessageBox.warning(self, "Warning", "No original tweet to reply to.")
            return

        # Create a prompt for the Claude API to generate a response
        prompt = f"Original Tweet: {self.original_text}\nHey Claude, can you reply to this comment in a way that sounds natural and friendly, as if a person were saying it casually over text? Show a bit of personality, but don’t be overly formal or stiff. Keep it real. Don't be too enthusiastic or too negative. Just be chill and friendly."

        # Call the API to get replies
        suggestions = self.call_claude_api(prompt)

        if suggestions:
            # Clear any existing buttons
            for i in reversed(range(self.buttons_layout.count())):
                widget = self.buttons_layout.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)

            # Create buttons for each suggestion using QFrame and QLabel
            for idx, suggestion in enumerate(suggestions):
                reply_frame = QFrame()
                reply_layout = QHBoxLayout()
                reply_label = QLabel(suggestion)
                reply_label.setFont(QFont('Helvetica Neue', 14))
                reply_label.setWordWrap(True)
                reply_frame.setCursor(QCursor(Qt.PointingHandCursor))
                reply_frame.mousePressEvent = lambda event, s=suggestion: self.save_reply(s)

                reply_layout.addWidget(reply_label)
                reply_frame.setLayout(reply_layout)
                self.buttons_layout.addWidget(reply_frame)

            # Add the "No Response" button
            no_response_frame = QFrame()
            no_response_layout = QHBoxLayout()
            no_response_label = QLabel("No Response")
            no_response_label.setFont(QFont('Helvetica Neue', 14))
            no_response_frame.setCursor(QCursor(Qt.PointingHandCursor))
            no_response_frame.mousePressEvent = self.no_response

            no_response_layout.addWidget(no_response_label)
            no_response_frame.setLayout(no_response_layout)
            self.buttons_layout.addWidget(no_response_frame)
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
                suggestions = [line.strip() for line in text.split('\n') if line.strip()]
                return suggestions[:3]
        else:
            QMessageBox.critical(self, "API Error", f"Error: {response.status_code}, {response.text}")
        return []

    def save_reply(self, selected_reply):
        output_data = {
            'original_tweet': self.original_text,
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

    def no_response(self):
        QMessageBox.information(self, "No Response", "You have chosen not to respond.")
        # Optionally, you can perform any action here if needed

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TweetResponder()
    window.show()
    sys.exit(app.exec_())