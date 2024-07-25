import multiprocessing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def load_words(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]


def save_to_file(content, output_file):
    with open(output_file, 'a', encoding='utf-8') as file:
        file.write(content + '\n')


def scrape_words(words, output_file, failed_words_file):
    url_template = "https://english-military-dictionary.org.ua/{}"

    # Setup Chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run headless Chrome to not open a browser window
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    try:
        for word in words:
            url = url_template.format(word)
            print(url)
            driver.get(url)

            try:
                # Wait for the element to be present and get the text
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div/div/main/div/article/p/span"))
                )
                text = element.text

                # Save the word and the extracted text to the file
                save_to_file(f"{word} - {text}", output_file)
                print(f"Saved content for {word}")
            except Exception as e:
                print(f"Failed to extract content for {word}: {e}")
                # Write the failed word immediately to the file
                save_to_file(word, failed_words_file)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


def main():
    words = load_words('modified_words.txt')
    output_file = 'extracted_content.txt'
    failed_words_file = 'failed_words.txt'

    # Clear the output files if they exist
    open(output_file, 'w').close()
    open(failed_words_file, 'w').close()

    # Split words into two parts
    mid_index = len(words) // 2
    words_part1 = words[:mid_index]
    words_part2 = words[mid_index:]

    # Create processes
    process1 = multiprocessing.Process(target=scrape_words, args=(words_part1, output_file, failed_words_file))
    process2 = multiprocessing.Process(target=scrape_words, args=(words_part2, output_file, failed_words_file))

    # Start processes
    process1.start()
    process2.start()

    # Wait for processes to complete
    process1.join()
    process2.join()


if __name__ == "__main__":
    main()
