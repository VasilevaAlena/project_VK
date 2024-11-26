import requests
from dotenv import load_dotenv
import os.path
from pprint import pprint
import json
from tqdm import tqdm
from time import sleep
import logging


logging.basicConfig(level='DEBUG', filename="py_log.log", filemode="w", format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()
logging.getLogger('urllib3').setLevel('CRITICAL')


dotenv_path = 'config.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


vk_token = os.getenv('VK_TOKEN')
ya_token = os.getenv('YA_TOKEN')


class VKСonnection:
    def __init__(self, access_token, version='5.199'):
        self.access_token = access_token
        self.version = version
        self.base_url = 'https://api.vk.com/method/'
        self.params = {
            'access_token': self.access_token,
            'v': self.version
        }


    def get_info_all_photo_profile(self, user_id): 
        """ функция для получения данных о фотографиях с профиля"""
        logger.debug(f'Enter in the get_info_all_photo_profile function: user_id = {user_id}')
        url = f'{self.base_url}photos.get'
        params = {
            **self.params,
            'owner_id': user_id,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1
        }
        response = requests.get(url, params=params)
        logger.error(f"function: get_info_all_photo_profile. response.status_code = {response.status_code}")
        if 200 <= response.status_code < 300: # проверка успешен ли запрос
            data_photos = response.json()['response']['items']
            return data_photos
        else:
            logger.error(f"function: get_info_all_photo_profile. response.status_code = {response.status_code}")
            return f'Ошибка при получении данных о фотографиях - {response.status_code}'
    

    def get_info_all_photo_wall(self, user_id): 
        """функция для получения данных о фотографиях со стены"""
        logger.debug(f'Enter in the get_info_all_photo_wall function: user_id = {user_id}')
        url = f'{self.base_url}photos.get'
        params = {
            **self.params,
            'owner_id': user_id,
            'album_id': 'wall',
            'photo_sizes': 1,
            'extended': 1
        }
        response = requests.get(url, params=params)
        logger.error(f"function: get_info_all_photo_wall. response.status_code = {response.status_code}")
        if 200 <= response.status_code < 300: # проверка успешен ли запрос
            data_photos = response.json()['response']['items']
            return data_photos
        else:
            logger.info(f"function: get_info_all_photo_wall. An INFO - Ошибка при получении данных о фотографиях - {response.status_code}")
            return f'Ошибка при получении данных о фотографиях - {response.status_code}'
        

    def get_link_photo(self, data_photos): 
        """функция для получения ссылок на фотографии максимального размера"""
        logger.debug('Enter in the get_link_photo function')
        link_photo_max_size = {} # словарь, где ключ это ссылка на фото, а значение список из количество лайков и размера фото
        for photo in data_photos:
            like_photo = photo['likes']['count'] # эти данные нужны для названия фото
            size_photo = photo['sizes']
            id_photo = photo['id'] # для того чтобы не дублировать в альбоме фотографии в дальнейшем будет проверка на наличие фото по id
            for size in size_photo: # поиск фотографий максимального размера
                if size['type'] == 'z':
                    link_photo_max_size[id_photo] = [size['url'], f'{like_photo}.jpg', size['type']]
                elif id_photo not in link_photo_max_size and size['type'] == 'y':
                    link_photo_max_size[id_photo] = [size['url'], f'{like_photo}.jpg', size['type']]
                elif id_photo not in link_photo_max_size and size['type'] == 'x':
                    link_photo_max_size[id_photo] = [size['url'], f'{like_photo}.jpg', size['type']]
        return link_photo_max_size # возврат словаря со ссылками на фото и со значением количества лайков
    

    def create_folder_and_save_photo(self, link_photo_max_size, ya_token=ya_token, name_folder=str): 
        """функция для создания паки на Яндекс диске и сохранения фотографий"""
        logger.debug(f'Enter in the create_folder_and_save_photo function: link_photo_max_size = {link_photo_max_size}')
        url_create_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': name_folder}
        headers = {'Authorization': ya_token}
        requests.put(url_create_folder, params=params, headers=headers) # проверка raise_for_status() здесь не нужна, так как папка уже может быть создана
        url_download_request = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        for file_name in link_photo_max_size.values():
            params = {
            'url': file_name[0],
            'path': name_folder + "/" + file_name[1]
        }
            headers = {'Authorization': ya_token}
            response = requests.post(url_download_request, params=params, headers=headers)
            logger.error(f"function: create_folder_and_save_photo. response.status_code(save_photo) = {response.status_code}")
            response.raise_for_status() 
            response.json()['href']
            for progress in tqdm(file_name):
                sleep(0.5)
                print(progress)
        logger.info("function: create_folder_and_save_photo. An INFO - Фотографии успешно загружены в созданной папке")
        return "Фотографии успешно загружены в созданной папке"


    def get_json_photos(self, link_photo_max_size): 
        """Функция создания Json файла"""
        logger.debug('Enter in the get_json_photos function')
        json_file = []
        for file_name in link_photo_max_size.values():
            json_dict = {}
            json_dict["file_name"] = file_name[1]
            json_dict["size"] = file_name[2]
            json_file.append(json_dict)
        return json_file

    def save_json(self, json_file, name_file=str): 
        """Функция записи в файл Json данных о фотографиях"""
        logger.debug(f'Enter in the save_json function: json_file = {json_file}')
        with open(name_file, 'w', encoding='utf8') as f:
            json.dump(json_file, f, indent=2)
            logger.info("function: save_json. An INFO - Json файл создан")
        return "Json файл создан"


connect = VKСonnection(vk_token)
user_photos_profile = connect.create_folder_and_save_photo(connect.get_link_photo(connect.get_info_all_photo_profile(154010681)), name_folder='Photo_VK_profile')
save_json_file = connect.save_json(connect.get_json_photos(connect.get_link_photo(connect.get_info_all_photo_profile(154010681))), 'Photos_profile.json')
user_photos_wall = connect.create_folder_and_save_photo(connect.get_link_photo(connect.get_info_all_photo_wall(154010681)), name_folder='Photo_VK_wall')
save_json_file = connect.save_json(connect.get_json_photos(connect.get_link_photo(connect.get_info_all_photo_wall(154010681))), 'Photos_wall.json')


