Я вообщем попробовал засунуть Flask в App, нашел в интернете. Вроде работает. Проект запускается через запуск app через python.

Примеры команд для тестирования API:

POST: curl -X POST http://127.0.0.1:5000/api/orders \
-H "Content-Type: application/json" \
-d '{
  "amount": 500,
  "profit": 100,
  "quantity": 5,
  "customer_id": 1,
  "sub_category_id": 1,
  "payment_mode_id": 1,
  "order_date": "2026-03-27"
}'
PUT: curl -X PUT http://127.0.0.1:5000/api/orders/151 \
-H "Content-Type: application/json" \
-d '{
  "amount": 600,
  "profit": 120
}'
DELETE: curl -X DELETE http://127.0.0.1:5000/api/orders/151
GET: curl -X GET http://127.0.0.1:5000/api/orders
GET для одного: curl -X GET http://127.0.0.1:5000/api/orders/151
