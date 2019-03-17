import pika

DEFAULT_EXCHANGE = "MainData"

def initial_config():

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange=DEFAULT_EXCHANGE)

    connection.close()

def delete_all():
    pass

def purge_all():
    pass