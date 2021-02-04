import requests
from  bs4 import BeautifulSoup
import json
import re
import time
import html
import dateparser
from uuid import uuid4
from typing import List, Dict, Optional
import pandas as pd

soup = None
lagos_hotels = "https://hotels.ng/hotels-in-lagos"

hotels_response = requests.get(lagos_hotels)
pages_on_hotel = None

hotel_url = None
hotel_name = None
# reviews_json = None
# reviews_string = None
# reviews_soup = None
reviews = None
person_reviews = None

def clean_reviews(reviews_list: List):
  """
    This function removes all the HTML tags in a review

    Args
        reviews_list: A list containing Reviews

    Returns:
        List: A List containing the cleaned Reviews
    """
  cleaned_reviews = []
  if reviews_list:
    for review in reviews_list:
      cleaned_reviews.append(review.text)
  return cleaned_reviews

def get_hotel_names(hotel_list):
  hotels = []
  if hotel_list:
    for hotel in hotel_list:
      hotels.append(hotel.text)
  return hotels


def get_hotels_from_page(page_url: str) -> Dict:
  """
    This function gets the Hotel names, URLs and review Url of hotel from a page

    Args
        page_url: the Url of the page where hotels

    Returns:
        Dict: A Dictionary containing the Hotel names, Hotel URL, and Hotel Reviews page
    """
  start = time.time()
  pages_on_hotel = None

  hotel_dict = {}
  hotel_url = None
  hotel_name = None
  hotels_response = requests.get(page_url)

  try:
    if hotels_response.status_code == 200:
      soup = BeautifulSoup(hotels_response.content)

      hotel_divs = soup.find_all(class_="listing-hotels-details-property")

      for hotel_div in hotel_divs:
        hotel_url = hotel_div.a['href']
        hotel_name = hotel_div.h2.text
        hotel_review_url = f'{hotel_url}/reviews'

        hotel_dict[str(uuid4())] = {'url': hotel_url, 'hotel_name' : hotel_name, 'review_url' : hotel_review_url}

  except Exception as e:
    print(e)

  start = time.time()


# end

  print(f'(get_hotels_from_page) Time: {time.time() - start}')
  return hotel_dict

def get_reviews_from_hotel(hotels_dict: Dict) -> List[pd.DataFrame]:
    """
    This function gets the Reviews from a hotel reviews page

    Args
        hotels_dict: the Dictionary that contains the Hotesl information

    Returns:
        List: A List containing the Hotels and metadata
    """
    start = time.time()

    reviews_list = None
    person_reviews_list = None

    cleaned_review_list = []
    cleaned_person_reviews_list = []

    df = None
    df_list = []

    for id, review_details in hotels_dict.items():
      response = requests.get(review_details['review_url'])
      try:
        if response.status_code == 200:
          reviews_soup = BeautifulSoup(response.content)

          reviews_list = reviews_soup.select("article > p[class='']")
          person_reviews_list = reviews_soup.select("article > p[class=sph-reviews-person]")

        if reviews_list and person_reviews_list:
          for review, person in zip(reviews_list, person_reviews_list):
            cleaned_review_list.append(review.text)
            cleaned_person_reviews_list.append(person.text)

          df = pd.DataFrame({"reviews": cleaned_review_list, "person_reviews_list": cleaned_person_reviews_list})
          df['id'] = id
          df[['name', 'created_at']] = df['person_reviews_list'].str.split("\son\s", expand=True)
          df['name'] = df.name.str.replace('by\s', '')
          df['created_at'] = df['created_at'].apply(dateparser.parse)

          df = df[['id', 'name', 'reviews', 'created_at']]
          df_list.append(df)

      except Exception as e:
        print(e)
    print(f'(get_reviews_from_hotel) Time: {time.time() - start}')

    return df_list
