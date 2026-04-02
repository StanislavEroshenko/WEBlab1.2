Я вообщем попробовал засунуть Flask в App, нашел в интернете. Вроде работает. Проект запускается через запуск app через python.

Примеры команд для тестирования API:

POST: curl -u student:dvfu -i -H "Content-Type: application/json" --data '{"title":"China-Tower","type_building_id":1,"city_id":1,"year":2018,"height":500}' http://localhost:5000/api/v1/buildings/
PUT: curl -u student:dvfu -i -X PUT -H "Content-Type: application/json" --data '{"title":"China-Tower-Updated","type_building_id":1,"city_id":1,"year":2019,"height":510}' http://localhost:5000/api/v1/buildings/1
DELETE: curl -u student:dvfu -i -X DELETE http://localhost:5000/api/v1/buildings/1
GET: curl -i http://localhost:5000/api/v1/buildings/
GET для одного: curl -i http://localhost:5000/api/v1/buildings/2
