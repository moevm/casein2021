# Lapis CASE-IN 2021

## Короткое описание  
Решение команды Lapis в рамках соревнования Case-in 2021 в лиге "Цифровой атом" по кейсу "Дистанционная адаптация новых сотрудников".  
Проект представляет собой корпоративную образовательную платформу с курсами, прохождение которых помогает новому сотруднику адаптироваться в новой компании.  
  
## Запуск  
  
В приложении курсы хранятся в зашифрованном виде, поэтому изначально необходимо установить ключ шифрования в качестве переменной среды.  
```bash
export ENCRYPT_KEY='\<KEY\>'  
```  
Необходимо наличие docker-compose. Установка подробно описана в [этой инструкции](https://docs.docker.com/compose/install/)
После этого достаточно запустить следующую команду (находясь в корневой директории)  
```bash
docker-compose up 
```  
И перейти по адресу localhost:5000 в браузере.  
  
## Технологии  
В приложении использовались:
* [Flask](https://flask.palletsprojects.com/en/1.1.x/)
* [Mongo](https://www.mongodb.com/)
* [Bootstrap 5](https://getbootstrap.com/docs/5.0/getting-started/introduction/)
* [jQuery](https://jquery.com/)  
  
## Авторы  
* **Дмитрий Иванов** - [HadronCollider](https://github.com/HadronCollider)
* **Максим Доброхвалов** - [Nightbot1448](https://github.com/Nightbot1448)
* **Никита Ваганов** - [justaleaf](https://github.com/justaleaf)
