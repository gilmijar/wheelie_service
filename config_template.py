"""For new installation clone me as config.py and fill with proper values (usernam, host, pass etc.)"""
ip = '192.168.1.1'
port = 3306
user = 'user_name'

service_rate_groups = {#car_id: base_service_price
    2: 1,
    3: 1,
    4: 1,
    1: 1,
    6: 2,
    5: 2,
    9: 2,
    10: 2,
    7: 3,
    12: 3,
    8: 3,
    11: 3
}
service_rates = (100, 150, 200)
service_rate_change = 0.05
