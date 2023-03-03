from selenium_base import driver_creation
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from tqdm import tqdm
import re
import random
import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

'''
I need someone to scrape all of the advisors off of this list, there are 60,052 RESULTS to excel

https://www.letsmakeaplan.org/find-a-cfp-professional?limit=10&pg=1&randomKey=614&sort=random&distance=100#


I think we'll be able to extract the following information which seems important to me:
1. Postal code (first 5 characters) -- check
2. States (can be more than one) -- check
3. Cities and States (can be more than one) -- check
4. Full name -- check
5. First name -- check
6. Last name -- check
7. Mid name (if there) -- check
8. Perfered designation (Mr./Ms., etc) -- check
7. Organization name -- check
8. Certification status -- check
9. Website -- check
10. LinkedIn url -- check
11. Phone numbers (can be more than one) -- check
12. Languages (can be more than one) -- 
13. Expertise (can be more than one) -- 
14. Planning services (can be more than one) --
15. Minimum assets -- 
16. Certification status -- check
17. Latitude longitude (can be more than one)



For address, the format needs to be:
1. Address line 1
2. City
3. State
4. Postal code (complete)

Also, note that the above values can be missing on the site and hence missing in our excel

There will be a bonus if you can extract email addresses.

completed after a 2 weeks, light work throughout. Aside from some very few edge cases, database would be complete and 
actionable in ~95 hours.
'''


def profile(driver):
    # print(driver.current_url)
    time.sleep(3)
    try:
        website = None
        contents = re.findall('http+[a-zA-z:/.\-?=_]+',
                              driver.find_element(By.CSS_SELECTOR, '.hero-profile-content').text)
        if len(contents) > 0:
            website = contents
    except Exception as e:
        website = None

    title_name_raw = re.findall('[a-zA-Z.]+', driver.find_element(By.CSS_SELECTOR, '.hero-profile-name').text)
    company = driver.find_element(By.CSS_SELECTOR, '.info-inner > p:nth-child(1)').text
    address = driver.find_element(By.CSS_SELECTOR, '.info-inner > p:nth-child(2)').text
    city_state_postal = driver.find_element(By.CSS_SELECTOR, '.info-inner > p:nth-child(3)').text

    try:
        phone_number = driver.find_element(By.CSS_SELECTOR, '.info-inner > p:nth-child(4)').text
    except Exception as e:
        phone_number = None

    certification_year = re.findall('[0-9]+', driver.find_element(By.CSS_SELECTOR, '.profile-section-year').text)

    try:
        linkedin = driver.find_element(By.CSS_SELECTOR, '.hero-profile-image').get_attribute('href')
    except Exception as e:
        linkedin = None
        print(e)
    child = 2

    professional_information = []

    while True:
        try:
            professional_information.append(
                driver.find_element(By.CSS_SELECTOR, f'div.profile-section:nth-child({child})'))
            child += 1
        except NoSuchElementException:
            break

    client_focus, planning_services, min_assets, langs = [], [], [], []

    for elem in professional_information:
        if elem.find_element(By.TAG_NAME, 'h3').text != 'Year CFP® Certification Received':
            heading = elem.find_element(By.TAG_NAME, 'h3').text
            list = elem.find_element(By.TAG_NAME, 'ul')
            contents = list.find_elements(By.TAG_NAME, 'li')
            for elem in contents:
                if heading == 'Client Focus':
                    client_focus.append(elem.text)
                elif heading == 'Planning Services Offered':
                    planning_services.append(elem.text)
                elif heading == 'Your Minimum Investable Assets':
                    min_assets.append(elem.text)
                elif heading == 'Languages':
                    langs.append(elem.text)
                else:
                    pass

    if '.' in title_name_raw[0] or 'MISS' == title_name_raw[0]:
        des, first, last = title_name_raw[0], title_name_raw[1], title_name_raw[-1]
    else:
        des, first, last = None, title_name_raw[0], title_name_raw[-1]

    professional_entry = pd.Series({'city_state_postal': city_state_postal, 'address': address,
                                    'full_name': ' '.join(title_name_raw), 'first_name': first,
                                    'last_name': last, 'preferred_designation': des,
                                    'organization_name': company, 'certification_status': certification_year,
                                    'website': website, 'linkedin_url': linkedin,
                                    'phone_number': phone_number, 'languages': langs,
                                    'client_focus': client_focus, 'planning_services': planning_services,
                                    'minimum_assets': min_assets})

    return professional_entry


if __name__ == '__main__':
    profs_init = []

    with open('professionals.txt', 'r') as fp:
        for line in fp:
            x = line[:-1]
            profs_init.append(x)

    fp.close()

    profs = []

    [profs.append(x) for x in profs_init if x not in profs]

    driver = driver_creation()

    driver.get(profs[0])
    time.sleep(20)

    headings = ['city_state_postal', 'address', 'full_name', 'first_name', 'last_name',
                'preferred_designation', 'organization_name', 'certification_status', 'website', 'linkedin_url',
                'phone_number', 'languages', 'client_focus', 'planning_services', 'minimum_assets']
    professional_composite = pd.DataFrame(columns=headings)

    val = 0

    for professional in tqdm(profs):
        driver.get(professional)
        professional_composite = pd.concat([professional_composite, profile(driver).to_frame().T], ignore_index=True)
        # val += 1
        # if val % 10 == 0:
        #     print(professional_composite)

    professional_composite.to_csv('professional_profiles.csv', index=False)



