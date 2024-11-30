import requests
from dotenv import load_dotenv
import os.path
from pprint import pprint
import json
from tqdm import tqdm
from time import sleep
import logging
import datetime


logging.basicConfig(level='DEBUG', filename="py_log.log", filemode="w", format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()
logging.getLogger('urllib3').setLevel('CRITICAL')


dotenv_path = 'config.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


vk_token = os.getenv('VK_TOKEN')
ya_token = os.getenv('YA_TOKEN')


class VKСonnection:
    def __init__(self, vk_token=vk_token, ya_token=ya_token, version='5.199'):
        self.vk_token = vk_token
        self.version = version
        self.base_url_vk = 'https://api.vk.com/method/'
        self.params = {
            'access_token': self.vk_token,
            'v': self.version
        }
        self.ya_token = ya_token


    def get_link_photo_max_size(self, user_id, album_id=str): 
        """ функция для получения данных о фотографиях с профиля, нахождение фото максимального размера и ссылку на него"""
        logger.debug(f'Enter in the get_link_photo_max_size function: user_id = {user_id}, album_id = {album_id}')
        url = f'{self.base_url_vk}photos.get'
        params = {
            **self.params,
            'owner_id': user_id,
            'album_id': album_id,
            'photo_sizes': 1,
            'extended': 1
        }
        response = requests.get(url, params=params)
        logger.error(f"function: get_link_photo_max_size. response.status_code = {response.status_code}")
        if 200 <= response.status_code < 300: # проверка успешен ли запрос
            data_photos = response.json()['response']['items']
            link_photo_max_size = {} # словарь, где ключ это ссылка на фото, а значение список из количество лайков и размера фото
            for photo in data_photos:
                like_photo = photo['likes']['count'] # эти данные нужны для названия фото
                size_photo = photo['sizes']
                date_photo = photo['date']
                dt = datetime.datetime.fromtimestamp(date_photo)
                dt_format = dt.strftime('%d%m%Y') 
                # name_photo = f'{like_photo}.jpg'
                name_photo_date = f'{like_photo}_{dt_format}.jpg'
                size_dict = {} # словарь, где ключ это тип размера фото, а значение высота умноженная на ширину
                for size in size_photo:
                    max_photo = size['height'] * size['width']
                    size_dict[size['type']] = [max_photo]
                    max_size = max(size_dict, key=size_dict.get) # нахождение мах типа фото исходя из мах значения
                    if max_size == size['type']:
                        link_photo_max_size[name_photo_date] = [size['url'], size['type']]
            return link_photo_max_size # возврат словаря со ссылками на фото и со значением количества лайков
        else:
            logger.error(f"function: get_link_photo_max_size. response.status_code = {response.status_code}")
            return f'Ошибка при получении данных о фотографиях - {response.status_code}'
    

    def create_folder_and_save_photo(self, link_photo_profile, name_folder=str): 
        """функция для создания папки на Яндекс диске, сохранения фотографий в ней, с сохранением файла Json с данными о загруженных фотографиях"""
        logger.debug(f'Enter in the create_folder_and_save_photo function: name_folder = {name_folder}, link_photo_max_size = {link_photo_profile}')
        url_create_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': name_folder}
        headers = {'Authorization': ya_token}
        requests.put(url_create_folder, params=params, headers=headers) # проверка raise_for_status() здесь не нужна, так как папка уже может быть создана
        url_download_request = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        json_file = []
        for file_name, date in link_photo_profile.items():
            params = {
            'url': date[0],
            'path': name_folder + "/" + file_name
        }
            headers = {'Authorization': ya_token}
            response = requests.post(url_download_request, params=params, headers=headers)
            logger.error(f"function: create_folder_and_save_photo. response.status_code(save_photo) = {response.status_code}")
            response.raise_for_status() 
            response.json()['href']
            for progress in tqdm(file_name):
                sleep(0.3)
                print(progress)
            json_dict = {}
            json_dict["file_name"] = file_name
            json_dict["size"] = date[1]
            json_file.append(json_dict)

        name_file = f'{name_folder}.json' 
        with open(name_file, 'w', encoding='utf8') as f:
            json.dump(json_file, f, indent=2)
            logger.info(f"function: save_json. An INFO - {name_folder} Json file created")
        return "Json файл создан"


connect = VKСonnection()
link_photo_profile = connect.get_link_photo_max_size(154010681, 'profile')
link_photo_wall = connect.get_link_photo_max_size(154010681, 'wall')
save_photo = connect.create_folder_and_save_photo(link_photo_profile, name_folder='Photo_VK_profile')
save_photo_wall = connect.create_folder_and_save_photo(link_photo_wall, name_folder='Photo_VK_wall')
