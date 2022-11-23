from my_token_vk import TOKEN_VK
from my_token import TOKEN_YA
import requests
import datetime
import json
from tqdm import tqdm

def find_max_size(dict_in_search):
    max_size = 0
    need_elem = 0
    for j in range(len(dict_in_search)):
        file_size = dict_in_search[j].get('width') * dict_in_search[j].get('height')
        if file_size > max_size:
            max_size = file_size
            need_elem = j
    return dict_in_search[need_elem].get('url'), dict_in_search[need_elem].get('type')

def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time

class Vk_Request:
    def __init__(self, token, user_id, version='5.131'):
        self.token = TOKEN_VK
        self.id = user_id
        self.version = version
        self.start_params = {'access_token': self.token, 'v': self.version}
        self.json, self.export_dict = self._dict_param()

    def _get_photo_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id,
                  'album_id': 'profile',
                  'photo_sizes': 1,
                  'extended': 1,
                  'rev': 1,
                  'count': 100
                  }
        if requests.get(url, params={**self.start_params, **params}).status_code == 200:
            photo_info = requests.get(url, params={**self.start_params, **params}).json()['response']
            return photo_info['count'], photo_info['items']
        else:
            print('Ошибка доступа к ВК')
            exit()

    def _get_dict_photo(self):
        photo_count, photo_items = self._get_photo_info()
        result = {}
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = find_max_size(photo_items[i]['sizes'])
            time_warp = time_convert(photo_items[i]['date'])
            new_value = result.get(likes_count, [])
            new_value.append({'likes_count': likes_count,
                              'add_name': time_warp,
                              'url_picture': url_download,
                              'size': picture_size})
            result[likes_count] = new_value
        return result

    def _dict_param(self):
        json_list = []
        sort_dict = {}
        picture_dict = self._get_dict_photo()
        for elem in picture_dict.keys():
            counter = 0
            for value in picture_dict[elem]:
                if len(picture_dict[elem]) == 1:
                    file_name = f'{value["likes_count"]}.jpeg'
                    sort_dict[file_name] = picture_dict[elem][0]['url_picture']
                else:
                    file_name = f'{value["likes_count"]} {value["add_name"]}.jpeg'
                    sort_dict[file_name] = picture_dict[elem][counter]['url_picture']
                    counter += 1
                json_list.append({'file name': file_name, 'size': value["size"]})
        return json_list, sort_dict

class Yandex:
    def __init__(self, folder_name, num=5):
        self.token = TOKEN_YA
        self.added_files_num = num
        self.url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.headers = {'Authorization': self.token}
        self.folder = self._create_folder(folder_name)

    def _create_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        if requests.get(url, headers=self.headers, params=params).status_code != 200:
            requests.put(url, headers=self.headers, params=params)
            print(f'\nПапка {folder_name} успешно создана в корневом каталоге Яндекс диска\n')
        else:
            print(f'\nПапка {folder_name} уже существует.\n')
        return folder_name

    def _in_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        resource = requests.get(url, headers=self.headers, params=params).json()['_embedded']['items']
        in_folder_list = []
        for elem in resource:
            in_folder_list.append(elem['name'])
        return in_folder_list

    def create_copy(self, dict_files):
        files_in_folder = self._in_folder(self.folder)
        copy_counter = 0
        if self.added_files_num >= len(dict_files):
            added_num = len(dict_files)
        else:
            added_num = self.added_files_num
        for key, i in zip(dict_files.keys(), tqdm(range(added_num))):
            if copy_counter < added_num:
                if key not in files_in_folder:
                    params = {'path': f'{self.folder}/{key}',
                              'url': dict_files[key],
                              'overwrite': 'false'}
                    requests.post(self.url, headers=self.headers, params=params)
                    copy_counter += 1
                else:
                    tqdm.write(f'Файл {key} уже существует')
            else:
                break

        print(f'\nЗапрос завершен, новых файлов скопировано: {copy_counter}'
              f'\nВсего файлов в исходном альбоме VK: {len(dict_files)}')

if __name__ == '__main__':

    id = input('Введите id пользователя в ВК ')
    try:
        my_VK = Vk_Request(TOKEN_VK, id)
    except:
        print('Профиль закрыт или не существует.')
        exit()
    with open('my_VK.json', 'w') as outfile:
        json.dump(my_VK.json, outfile)

    my_yandex = Yandex('VK photo', 5)
    my_yandex.create_copy(my_VK.export_dict)