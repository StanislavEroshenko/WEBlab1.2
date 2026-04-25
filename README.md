Я вообщем попробовал засунуть Flask в App, нашел в интернете. Вроде работает. Проект запускается через запуск app через python.

Примеры команд для тестирования API:

POST: curl -u student:dvfu -X POST http://localhost:5000/api/v1/buildings/ \
-H "Content-Type: application/json" \
-d "{\"title\":\"Test Tower\",\"type_building_id\":1,\"city_id\":1,\"year\":2020,\"height\":300}"

PUT: curl -u student:dvfu -X PUT http://localhost:5000/api/v1/buildings/1 \
-H "Content-Type: application/json" \
-d "{\"title\":\"Updated Tower\",\"type_building_id\":1,\"city_id\":1,\"year\":2022,\"height\":350}"

DELETE: curl -u student:dvfu -X DELETE http://localhost:5000/api/v1/buildings/1

GET: curl http://localhost:5000/api/v1/buildings/

GET для одного: curl http://localhost:5000/api/v1/buildings/1
