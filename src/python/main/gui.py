import sys, multiprocessing
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QTextEdit, QSizePolicy)
from PyQt5.QtGui import QFont, QIcon, QCursor, QPixmap, QColor
from PyQt5.QtCore import Qt

class TweetFrame(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("tweetFrame")
        layout = QVBoxLayout()

        # Profile picture
        profile_pic = QLabel()
        pixmap = QPixmap("default_profile.png")
        if pixmap.isNull():
            pixmap = QPixmap(48, 48)
            pixmap.fill(QColor("#1DA1F2"))
        profile_pic.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        profile_pic.setFixedSize(48, 48)
        profile_pic.setStyleSheet("border-radius: 24px; background-color: #2F3336;")

        # Username and handle
        user_info = QLabel("Username @handle")
        user_info.setStyleSheet("color: #8899A6; font-size: 14px;")

        # Tweet text
        self.tweet_text = QLabel(text)
        self.tweet_text.setWordWrap(True)
        self.tweet_text.setStyleSheet("color: #FFFFFF; font-size: 16px;")

        header_layout = QHBoxLayout()
        header_layout.addWidget(profile_pic)
        header_layout.addWidget(user_info, 1)

        layout.addLayout(header_layout)
        layout.addWidget(self.tweet_text)

        self.setLayout(layout)
        self.setStyleSheet("""
            QFrame#tweetFrame {
                background-color: #15202B;
                border: 1px solid #38444D;
                border-radius: 12px;
                padding: 5px;
            }
        """)

class TweetResponder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tweet Responder")
        self.resize(600, 700)
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet("""
            QWidget {
                background-color: #15202B;
                color: #FFFFFF;
                font-family: "Helvetica Neue", Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
            }
            QFrame {
                background-color: #1DA1F2;
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #1A91DA;
            }
            QTextEdit {
                background-color: #253341;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        # Original Tweet Display
        self.tweet_frame = TweetFrame("Loading tweet...")
        main_layout.addWidget(self.tweet_frame)

        # Replies Buttons Layout
        self.buttons_layout = QVBoxLayout()
        main_layout.addLayout(self.buttons_layout)

        self.setLayout(main_layout)

        # Load the tweet data
        self.load_tweet()

        # Automatically generate replies
        self.generate_replies()

    def load_tweet(self):
        try:
            with open('/Users/jordanwhite/Library/Application Support/Electron/surfer_data/X Corp/Twitter Posts/twitter-001/twitter-001.json', 'r') as file:
                data = json.load(file)
            tweets = data.get('content', [])
            if tweets:
                most_recent_tweet = tweets[0]
                self.original_text = most_recent_tweet.get('text', '')
                self.tweet_timestamp = most_recent_tweet.get('timestamp', '')

                self.tweet_frame.tweet_text.setText(self.original_text)
            else:
                self.tweet_frame.tweet_text.setText("No tweets found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load tweet data: {str(e)}")
            print(f"Error details: {e}")  # For debugging

    def generate_replies(self):
        if not hasattr(self, 'original_text') or not self.original_text:
            QMessageBox.warning(self, "Warning", "No original tweet to reply to.")
            return

        # Create a prompt for the Claude API to generate a response
        prompt = f"Original Tweet: {self.original_text}\nHey Claude, can you reply to this comment in a way that sounds natural, as if a person were saying it casually over text? Show a bit of personality, but don't be overly formal or stiff. Keep it real. Don't be too enthusiastic or too negative. Just be chill and friendly."

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
        self.close()

    def no_response(self, event):
        QMessageBox.information(self, "No Response", "You have chosen not to respond.")
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TweetResponder()
    window.show()
    sys.exit(app.exec_())
