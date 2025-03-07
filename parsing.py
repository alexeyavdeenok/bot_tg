import requests
from bs4 import BeautifulSoup

def parse_timetable(url):
    # Отправляем GET-запрос
    response = requests.get(url)
    
    # Проверяем успешность запроса
    if response.status_code != 200:
        raise Exception(f"Ошибка доступа к странице: {response.status_code}")
    
    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Находим все таблицы с классом 'table timetable'
    tables = soup.find_all('table', {'class': 'table timetable'})
    
    result = []
    
    for table in tables:
        # Обрабатываем каждую таблицу
        rows = table.find_all('tr')
        
        for row in rows:
            # Пропускаем строки-заголовки
            if 'heading' in row.get('class', []):
                continue
                
            # Извлекаем ячейки
            cells = row.find_all(['td', 'th'])
            row_data = []
            
            for cell in cells:
                # Обработка объединенных ячеек (colspan)
                colspan = int(cell.get('colspan', 1))
                
                # Извлекаем текст и очищаем от лишних пробелов
                text = ' '.join(cell.stripped_strings)
                
                # Добавляем данные с учетом colspan
                row_data.extend([text] * colspan)
                
            if row_data:  # Игнорируем пустые строки
                result.append(row_data)
    
    return result

# Пример использования
url = "https://edu.sfu-kras.ru/timetable?group=%D0%9A%D0%9823-17%2F1%D0%B1+%282+%D0%BF%D0%BE%D0%B4%D0%B3%D1%80%D1%83%D0%BF%D0%BF%D0%B0%29"  # Замените на реальный URL
timetable_data = parse_timetable(url)

# Вывод результата
for row in timetable_data:
    print(row)