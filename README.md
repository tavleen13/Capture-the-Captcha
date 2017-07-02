The website (http://ceodelhi.gov.in/OnlineErms/electorsearchidcard.aspx) requires a Voter ID and a capcha to be entered to obtain user Information

The script enters the given ID and detects the capcha and send it as input to the website and gets the info in a Csv format.

The capcha is broken by taking the screenshot and reading from the cropped image of the capcha.

Python version 2.4

REQUIREMENTS
 1. Selenium
 2. Beautiful Soup
 3. Scipy
 4. Regex
 5. Tesseract
 6. PIL
