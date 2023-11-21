import config
import mariadb
import keyring
from typing import List
from collections import namedtuple
from datetime import date
from functools import lru_cache


@lru_cache(50)
def get_this(sql) -> List[namedtuple]:
    cursor.execute(sql)
    return cursor.fetchall()


def make_batches(data, batch_size=500):
    batches = []
    for batch_no in range(len(data) // batch_size + abs(0 ** (len(data) % batch_size) - 1)):
        start = batch_no*batch_size
        finish = batch_no*batch_size+batch_size
        batches.append(data[start:finish])
    return batches


def insert_these(sql, data):
    batches = make_batches(data, batch_size=200)
    from progress.bar import FillingSquaresBar
    bar = FillingSquaresBar(f'Inserting {len(batches)} batches', max=len(batches), suffix='%(percent)d%%')
    for batch in batches:
        bar.next()
        cursor.executemany(sql, batch)
        connection.commit()
    bar.finish()


def insert_services(data):
    sql = 'INSERT IGNORE INTO service (inventory_id, service_type, service_date, service_cost) VALUES(?, ?, ?, ?)'
    insert_these(sql, data)


def format_first_day(month, year):
    return f'{year:04}-{month:02}-01'


def get_inventory(month, year) -> List[namedtuple]:
    first_day = format_first_day(month, year)
    sql = f'''SELECT inventory_id, car_id FROM inventory
        WHERE create_date < '{first_day}' 
        AND (sell_price is null or last_update > '{first_day}')
    '''
    return get_this(sql)


def get_rented_cars(month, year) -> List[namedtuple]:
    first_day = format_first_day(month, year)
    sql = f'''SELECT rental_id,
        inventory_id,
        rental_date,
        return_date
        FROM rental
        WHERE '{first_day}' between rental_date and return_date
    '''
    return get_this(sql)


def print_list(my_list):
    print(*my_list, sep='\n')


def gen_service(month, year, service_type='service', base_price=None):
    inventory = get_inventory(month, year)
    car_lookup = {inv.inventory_id: inv.car_id for inv in inventory}
    rented_cars = get_rented_cars(month, year)
    inventory_lookup = {ren.rental_id: ren.inventory_id for ren in rented_cars}
    unrented = set(car_lookup) - set(inventory_lookup.values())
    if not base_price:
        service_rates = {k: config.service_rates[v-1] for k, v in config.service_rate_groups.items()}

        def calc_price(car_id):
            return round(service_rates.get(car_id) *
                         (1 + (year - 2015) * config.service_rate_change), 2)
    else:
        def calc_price(_):
            return round(base_price * (1 + (year - 2015) * config.service_rate_change), 2)
    actions = []
    day = date(year, month, 1)
    for veh in unrented:
        actions.append(
            (
                veh,
                service_type,
                day.isoformat(),
                calc_price(car_lookup[veh])
            )
        )
    for ret_date in set(ren.return_date for ren in rented_cars):
        returns = (ren.inventory_id for ren in rented_cars if ren.return_date == ret_date)
        for veh in returns:
            actions.append(
                (
                    veh,
                    service_type,
                    ret_date.isoformat(),
                    calc_price(car_lookup[veh])
                )
            )
    return actions


if __name__ == '__main__':
    connection = mariadb.connect(
        user=config.user,
        password=config.passwd,
        host=config.ip,
        port=config.port,
        database=config.database
    )
    cursor = connection.cursor(named_tuple=True)
    master_list = []
    for yr in range(2016, 2028):
        master_list.extend(gen_service(month=3, year=yr, service_type='tire change', base_price=150))
        master_list.extend(gen_service(month=11, year=yr, service_type='tire change', base_price=150))
        master_list.extend(gen_service(month=3, year=yr, service_type='oil service'))
        master_list.extend(gen_service(month=9, year=yr, service_type='oil service'))
    master_list = sorted(master_list, key=lambda x: (x[2], x[0]))
    insert_services(master_list)
    connection.close()
