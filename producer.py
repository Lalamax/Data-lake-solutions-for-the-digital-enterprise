from kafka import KafkaProducer
import pandas as pd
from json import dumps
import json
import threading
from time import sleep

# Producer pour chaque source
producer_transactions = KafkaProducer(
    bootstrap_servers=['ec2-13-39-24-144.eu-west-3.compute.amazonaws.com:9092'], 
    value_serializer=lambda x: dumps(x).encode('utf-8')
)
producer_logs = KafkaProducer(
    bootstrap_servers=['ec2-13-39-24-144.eu-west-3.compute.amazonaws.com:9092'], 
    value_serializer=lambda x: dumps(x).encode('utf-8')
)
producer_social = KafkaProducer(
    bootstrap_servers=['ec2-13-39-24-144.eu-west-3.compute.amazonaws.com:9092'], 
    value_serializer=lambda x: dumps(x).encode('utf-8')
)
producer_ads = KafkaProducer(
    bootstrap_servers=['ec2-13-39-24-144.eu-west-3.compute.amazonaws.com:9092'], 
    value_serializer=lambda x: dumps(x).encode('utf-8')
)

# Envoie des CSV
def send_csv_to_kafka(file_path, topic, producer):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        producer.send(topic, value=row.to_dict())
        sleep(1)
    print(f"Envoi terminé pour {topic}")

# Envoie des JSON
def send_json_to_kafka(file_path, topic, producer):
    with open(file_path) as f:
        data = json.load(f)
        for item in data:
            producer.send(topic, value=item)
            sleep(1)
    print(f"Envoi terminé pour {topic}")

# Envoie pareéllèle avec des threads
threads = [
    threading.Thread(target=send_csv_to_kafka, args=('web_logs.csv', 'logs_topic', producer_logs)),
    threading.Thread(target=send_csv_to_kafka, args=('transactions.csv', 'transactions_topic', producer_transactions)),
    threading.Thread(target=send_json_to_kafka, args=('social_data.json', 'social_data_topic', producer_social)),
    threading.Thread(target=send_json_to_kafka, args=('ad_campaigns.json', 'ad_campaigns_topic', producer_ads)),
]

# Démarrage des threads
for thread in threads:
    thread.start()

# Attendre la fin de tous les threads
for thread in threads:
    thread.join()

# Fermeture des producer
producer_transactions.close()
producer_logs.close()
producer_social.close()
producer_ads.close()

print("ca marche !!")
