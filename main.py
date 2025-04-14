import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Define "Good" and "Bad" keywords
good_keywords = ['growth', 'investment', 'success', 'increase', 'positive', 'rise', 'boost', 'upward']
bad_keywords = ['loss', 'decline', 'negative', 'problem', 'fall', 'drop', 'downward', 'crisis']

def categorize_title(title):
    """
    Categorize article titles into 'Good' or 'Bad' based on keywords.
    """
    # Convert title to lowercase for easier matching
    title_lower = title.lower()
    
    # Check for presence of positive keywords
    if any(keyword in title_lower for keyword in good_keywords):
        return 'Good'
    
    # Check for presence of negative keywords
    elif any(keyword in title_lower for keyword in bad_keywords):
        return 'Bad'
    
    # Default to 'Bad' if no keyword matches
    return 'Bad'

def get_news_data_selenium(stock_symbol):
    url = f"https://finance.yahoo.com/quote/{stock_symbol}/news?p={stock_symbol}"

    # Set up Chrome options for headless browsing (no GUI)
    options = Options()
    options.add_argument('--headless')  # Run headless (no GUI)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialize the WebDriver using ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the URL
        driver.get(url)

        # Wait for the headlines to be visible
        headlines = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'h3')))
        
        titles = []
        retries = 3  # Retry logic if stale element exception occurs

        for _ in range(len(headlines)):
            # Retry logic for stale elements
            for attempt in range(retries):
                try:
                    headlines = driver.find_elements(By.CSS_SELECTOR, 'h3')
                    for headline in headlines:
                        title = headline.text.strip()
                        # Skip empty titles
                        if not title:
                            continue
                        # Categorize the article as 'Good' or 'Bad'
                        category = categorize_title(title)
                        titles.append({'title': title, 'category': category})
                    break  # Break if no stale element error occurs
                except Exception as e:
                    print(f"Error on attempt {attempt+1} for stale element: {e}")
                    if attempt == retries - 1:
                        print("Max retries reached for this element.")
                    time.sleep(1)  # Sleep before retry

    except Exception as e:
        print(f"An error occurred: {e}")
        titles = []

    finally:
        # Clean up: Close the browser
        driver.quit()

    return titles

# Test with Apple (AAPL)
stock_symbol = "GOOG"
news_data = get_news_data_selenium(stock_symbol)

# Categorize and plot the data
categories = [article['category'] for article in news_data]

# Count occurrences of "Good" and "Bad"
good_count = categories.count('Good')
bad_count = categories.count('Bad')

# Plotting the binary classification as a bar chart
labels = ['Good', 'Bad']
counts = [good_count, bad_count]

plt.bar(labels, counts, color=['green', 'red'])
plt.title('Categorized News Articles for GOOG')
plt.ylabel('Number of Articles')
plt.show()

# Print out the categorized articles
for article in news_data:
    print(f"Title: {article['title']}")
    print(f"Category: {article['category']}")
    print("-" * 50)
