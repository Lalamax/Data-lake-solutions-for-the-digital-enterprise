from kafka import KafkaConsumer
from s3fs import S3FileSystem
import json
import threading

# consumer Kafka
consumer_transactions = KafkaConsumer(
    'transactions_topic',
    bootstrap_servers=['35.180.190.239:9092'],  # Adresse IP directe
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)
consumer_logs = KafkaConsumer(
    'logs_topic',
    bootstrap_servers=['35.180.190.239:9092'],  # Adresse IP directe
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)
consumer_social = KafkaConsumer(
    'social_data_topic',
    bootstrap_servers=['35.180.190.239:9092'],  # Adresse IP directe
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)
consumer_ads = KafkaConsumer(
    'ad_campaigns_topic',
    bootstrap_servers=['35.180.190.239:9092'],  # Adresse IP directe
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Connexion S3
s3 = S3FileSystem()

# Consommation et sauvegarde
def consume_and_save(consumer, bucket_path):
    for count, msg in enumerate(consumer):
        with s3.open(f"{bucket_path}/{msg.topic}_{count}.json", 'w') as file:
            json.dump(msg.value, file)
        print(f"Message sauvegardé dans {bucket_path}/{msg.topic}_{count}.json")

# threds en parrélléle
threads = [
    threading.Thread(target=consume_and_save, args=(consumer_transactions, "s3://kafka-ing-transactions")),
    threading.Thread(target=consume_and_save, args=(consumer_logs, "s3://kafka-ing-logs")),
    threading.Thread(target=consume_and_save, args=(consumer_social, "s3://kafka-ing-social-data")),
    threading.Thread(target=consume_and_save, args=(consumer_ads, "s3://kafka-ing-ad-campaigns")),
]

# Démarrage des threads
for thread in threads:
    thread.start()

# Attendre la fin de tous les threads
for thread in threads:
    thread.join()

print("ça marche !")
