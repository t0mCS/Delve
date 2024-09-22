import time
import os
from playwright.sync_api import sync_playwright, expect

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
