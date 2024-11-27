# Partie 1 : Conception du Data Lake

## 1. Contexte

### Livrables

- **Description détaillée de l’architecture du Data Lake :** Disponible dans la partie 1.2
- **Diagramme de flux de données :** Disponible dans la partie 1.2
- **Choix des technologies :** Disponible dans la partie 1.2

L'entreprise souhaite centraliser et analyser ses données provenant de différentes sources pour améliorer la prise de décisions commerciales. Ces données incluent :  

- Bases de données relationnelles  
- Logs de serveurs web  
- Données de médias sociaux  
- Flux de données en temps réel  

### Objectif du Data Lake

1. **Centralisation** des données provenant de diverses sources :  
	   - Structurées, semi-structurées et non structurées.  
1. **Analyse et visualisation** des données collectées.  
2. **Gouvernance, sécurité et qualité** des données.  

---

### 1.2 Conception de l'Architecture du Data Lake et choix des technologie

L'architecture du Data Lake repose sur **AWS** et les services suivants :

- **AWS S3** :
  - Stockage des données brutes et transformées dans des **buckets**.  
  - Offre une **scalabilité** et une **flexibilité** pour stocker de grandes quantités de données.  
  - Permet la gestion des différentes étapes de traitement des données.

- **Apache Kafka** :
  - Ingestion des données en temps réel.  
  - Sert de **système de messagerie distribuée** pour capter les flux de données (IoT, applications, systèmes transactionnels).  
  - Permet de gérer des **événements** à faible latence à grande échelle.

- **AWS Glue et Apache Spark** :
  - **AWS Glue** : Service managé pour l'intégration de données, permettant l'exécution de tâches **ETL** (Extract, Transform, Load).  
  - **Apache Spark** : Utilisé pour le **traitement massif** de données en batch ou en streaming, offrant une capacité de calcul parallèle sur de grandes volumétries de données.

- **AWS Athena** :
  - Permet l'**analyse ad hoc** des données stockées dans **S3**.  
  - Requêtes SQL directement sur des fichiers (CSV, Parquet, JSON, etc.) sans nécessiter de déplacer les données.  
  - Solution **serverless** pour des analyses rapides et flexibles.

- **API REST (Django)** :
  - Expose les données transformées via une **API REST** pour les utilisateurs finaux.  
  - Développée avec **Flask (Python)**, cette API permet des **requêtes HTTP** pour accéder aux données.
  - Sert d'interface entre le Data Lake et les outils des utilisateurs finaux.


### Architecture Globale
- L'ensemble des services AWS permet une **gestion fluide** du flux de données, de leur ingestion à leur visualisation.  
- L'infrastructure **scalable**, **haute disponibilité** et **sécurisée** assure une gestion optimale des données.  
- Les composants sont intégrés pour offrir un écosystème complet permettant une gestion efficace des données à chaque étape du processus.


### Diagramme de flux de données

![Architecture shéma](Pasted%20image%2020241125093537.png)

---

## 2. Création de l’Infrastructure 

### Livrables : 

- **Scripts de déploiement** pour l’infrastructure : 
	- Version manuelle : il suffit de suivre manuellement les instruction ci dessous en n'oubliant pas de generer une clé. Il est aussi possible de faire ces étapes AWS entierement sur le site AWS
	- Version Automatisée : Il faudra compiler le fichier main.tf grâce a terraform, ce script permet la configuration de nos topics et composant AWS.
- **Documentation technique sur les choix de technologies et de solutions Cloud**

## Choix de la solution

Nous avons opté pour une solution basée sur le cloud pour la création de notre infrastructure. Initialement, chaque service cloud était configuré manuellement. Cependant, nous avons décidé de développer des scripts d'Infrastructure as Code (IaC) pour :

- Créer et configurer les ressources AWS (par exemple, Kafka, S3, AWS Glue, EC2).
- Automatiser le déploiement pour rendre le processus reproductible.
- Assurer la cohérence de l'environnement en déployant toujours la même configuration.

## Configuration Manuelle de l'Infrastructure sur AWS

### Création de l'instance EC2
- Création d'une instance EC2 sur AWS pour héberger Kafka.
- Connexion à l'instance via SSH avec la clé d'accès :  
  `ssh -i "myKey.pem" ec2-user@ec2-35-180-87-153.eu-west-3.compute.amazonaws.com`

Ne pas oublier dans l'instance AWS :
Sécurité => groupe de sécurité => règle entrante => type anywhere et anywhere IPv4

### Installation de Java
```bash
sudo yum update
java -version
sudo yum install java-1.8.0-openjdk
sudo yum install -y https://d3pxv6yz143wms.cloudfront.net/8.302.08.1/amazon-corretto-8.302.08.1-linux-x64.rpm
sudo yum install -y java-1.8.0-amazon-corretto-devel
java -version
```

### Installation de Kafka
```bash
wget https://downloads.apache.org/kafka/3.9.0/kafka_2.12-3.9.0.tgz
tar -xvf kafka_2.12-3.9.0.tgz
cd kafka_2.12-3.9.0
```

### Configuration de Kafka
```bash
cd kafka_2.12-3.9.0
sudo nano config/server.properties
```
Modifier les lignes suivantes :
```
listeners=PLAINTEXT://localhost:9092
advertised.listeners=PLAINTEXT://<votre_IP_EC2>:9092
```

### Démarrage de ZooKeeper
```bash
bin/zookeeper-server-start.sh config/zookeeper.properties
```

### Démarrage de Kafka
Dans une nouvelle session SSH :
```bash
export KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"
cd kafka_2.12-3.9.0
bin/kafka-server-start.sh config/server.properties
```

### Création des topics Kafka
```bash
bin/kafka-topics.sh --create --topic transactions_topic --bootstrap-server 35.180.190.239:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create --topic logs_topic --bootstrap-server 35.180.190.239:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create --topic social_data_topic --bootstrap-server 35.180.190.239:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create --topic ad_campaigns_topic --bootstrap-server 35.180.190.239:9092 --partitions 1 --replication-factor 1
```

### Création des buckets S3
```bash
aws s3 mb s3://kafka-ing-transactions
aws s3 mb s3://kafka-ing-logs
aws s3 mb s3://kafka-ing-social-data
aws s3 mb s3://kafka-ing-ad-campaigns
```

### Lancement des scripts Python
Exécution des scripts `producer.py` et `consumer.py` pour envoyer et recevoir des messages de Kafka.

### Création des Crawlers AWS Glue
Création de 4 crawlers Glue pour explorer les données dans les différents buckets S3 :
- Un crawler pour chaque bucket (`kafka-ing-transactions`, `kafka-ing-logs`, `kafka-ing-social-data`, `kafka-ing-ad-campaigns`).
- Les crawlers analysent les données dans S3 et les stockent dans le catalogue Glue pour les rendre accessibles à Athena.

### Validation avec Athena
- Utilisation d'Athena pour interroger les données stockées dans S3 après leur préparation par AWS Glue.
- Lancer des requêtes SQL dans Athena pour valider et analyser les données traitées.

En conclusion, nous avons initialement envisagé d'utiliser Terraform pour faciliter le déploiement de notre infrastructure. Cependant, dans le cadre de ce projet, cette approche n'était pas nécessaire. Nous avons donc opté pour une configuration manuelle de l'infrastructure sur AWS, ce qui s'est avéré suffisant pour nos besoins actuels. Cette approche nous a permis de mettre en place rapidement notre environnement Kafka et de nous concentrer sur le traitement des données et leur analyse avec AWS Glue et Athena.


# Partie 2 : Ingestion et Transformation des Données

### Livrables : 

- **Pipeline d’ingestion en temps réel ou batch pour les différentes sources de données**
	- Producer.py
	- Consumer.py
- **Exemple de datasets ingérés dans le Data Lake**
	- Simulation des données : data_simulator.ipynb
	- Ingestion : Explication ci-dessous

## Pipeline d’Ingestion des Données en Temps Réel

Pour notre projet, nous avons conçu un pipeline d’ingestion de données en temps réel basé sur Kafka et le stockage AWS S3. L'objectif est de traiter simultanément des flux de données variés et de permettre une analyse rapide avec AWS Athena. Voici comment le pipeline est structuré :

### 1. Génération des Données Fictives

Nous avons utilisé la bibliothèque Python Faker pour simuler quatre jeux de données réalistes, permettant de tester et valider notre pipeline :

#### Données de Transactions

**Exemple :**

| ClientID                          | ClientName | TransactionDate | Product | Amount | PaymentMethod |
|-----------------------------------|------------|-----------------|---------|--------|---------------|
| 123e4567-e89b-12d3-a456-426614174000 | John Doe   | 2024-10-15      | WidgetX | 199.99 | Credit Card   |

**Description :** Ce dataset inclut 1 000 lignes de transactions, comprenant des informations telles que l’ID du client, le produit acheté, la date de transaction, le montant et le mode de paiement. Les données sont sauvegardées dans un fichier CSV (`transactions.csv`).

#### Logs de Serveur Web

**Exemple :**

| IP_Address    | URL   | Status_Code | Timestamp           |
|---------------|-------|-------------|---------------------|
| 192.168.1.10  | /home | 200         | 2024-11-05 10:22:15 |

**Description :** 1 000 logs générés aléatoirement avec l’adresse IP, l’URL visitée, le code de statut HTTP et un horodatage. Sauvegardés dans un fichier CSV (`web_logs.csv`).

#### Posts sur les Réseaux Sociaux

**Exemple :**

```json
{
    "user": "alice123",
    "message": "Découvrez notre nouveau produit ! #Innovation",
    "post_date": "2024-10-20",
    "likes": 120,
    "retweets": 30
}
```

**Description :** 1 000 posts contenant l'utilisateur, le message, la date de publication, le nombre de likes et de retweets. Sauvegardés dans un fichier JSON (`social_data.json`).

#### Campagnes Publicitaires

**Exemple :**

```json
{
    "campaign_id": "9e107d9d372bb6826bd81d3542a419d6",
    "start_date": "2024-10-01",
    "end_date": "2024-10-31",
    "budget": 5000.50,
    "clicks": 350,
    "impressions": 15000,
    "ctr": 0.0233
}
```

**Description :** 100 campagnes publicitaires avec l’ID de la campagne, les dates de début et de fin, le budget, le nombre de clics et d’impressions, ainsi que le taux de clics (CTR). Sauvegardés dans un fichier JSON (`ad_campaigns.json`).

### 2. Production des Données vers Kafka

Les données générées sont envoyées vers Kafka en temps réel via le script `producer.py`. Chaque type de données est envoyé vers un topic Kafka dédié :

- **Topics Kafka :**
  - `transactions_topic` : reçoit les données de transactions.
  - `logs_topic` : reçoit les logs de serveur.
  - `social_data_topic` : reçoit les posts des réseaux sociaux.
  - `ad_campaigns_topic` : reçoit les données des campagnes publicitaires.

Le script utilise des threads pour paralléliser l'envoi des données. Chaque producteur Kafka lit les fichiers (CSV/JSON), transforme les données en dictionnaire Python et envoie chaque entrée sous forme de message JSON vers Kafka.

### 3. Consommation des Données en Temps Réel

Le script `consumer.py` consomme les messages des topics Kafka et sauvegarde les données dans des buckets S3 pour une persistance et une analyse ultérieure :

- **Buckets S3 :**
  - `s3://kafka-ing-transactions` : pour les transactions.
  - `s3://kafka-ing-logs` : pour les logs.
  - `s3://kafka-ing-social-data` : pour les posts réseaux sociaux.
  - `s3://kafka-ing-ad-campaigns` : pour les campagnes publicitaires.

Les consommateurs Kafka sont configurés pour écouter en temps réel les messages de chaque topic et sauvegarder chaque message sous forme de fichiers JSON dans S3.

### 4. Analyse des Données avec AWS Athena

Une fois les données ingérées et stockées dans S3, elles sont prêtes pour l’analyse avec AWS Athena :

#### AWS Glue Crawler

Nous avons configuré des crawlers AWS Glue pour indexer automatiquement les fichiers dans S3 et mettre à jour le catalogue de données. Les tables Glue permettent une interrogation facile via SQL dans Athena.

#### Analyse avec Athena

**Exemples de requêtes possibles :**

- Analyse des ventes par produit et méthode de paiement.
- Identification des erreurs courantes dans les logs serveur (codes 4xx et 5xx).
- Suivi des performances des campagnes publicitaires (CTR, impressions).
- Analyse de l’engagement sur les réseaux sociaux (likes, retweets).

### En Résumé

Le pipeline combine l’ingestion en temps réel avec Kafka et le stockage persistant dans S3. Les scripts `producer.py` et `consumer.py` utilisent des threads pour une gestion parallèle des flux de données. AWS Glue et Athena facilitent l'analyse des données après ingestion. Cette architecture permet de traiter des flux de données variés et d’obtenir des insights rapidement.

Ce pipeline d’ingestion robuste nous permet de gérer des flux de données complexes en temps réel tout en garantissant une persistance durable et une capacité d'analyse avancée, répondant ainsi aux besoins de notre projet.

### Partie 3 : Analyse et Exploitation des Données

#### Livrables

- **Code API** : `myproject/`
- **Documentation des endpoints implémentés et les résultats qu’ils renvoient** : Disponible ci-dessous

### 1. API pour Exposer les Données Athena

Nous avons choisi Django pour notre API, celle-ci permet d'exposer les données stockées dans Athena en exécutant des requêtes SQL. Les résultats des requêtes sont retournés sous forme de JSON et peuvent être utilisés pour des analyses ou pour alimenter des tableaux de bord.

### Fonctionnalités principales :

- Connexion à Athena via Boto3.
- Exécution de requêtes SQL personnalisées.
- Gestion des résultats et des erreurs.

### Étapes de Fonctionnement

#### 1. Initialisation

- L'API utilise Django comme framework web.
- Le client Boto3 est configuré pour se connecter à Athena dans la région.
- Les buckets S3 associés sont définis pour :
    - Transactions : `s3://kafka-ing-transactions/`
    - Logs : `s3://kafka-ing-logs/`
    - Posts réseaux sociaux : `s3://kafka-ing-social-data/`
    - Campagnes publicitaires : `s3://kafka-ing-ad-campaigns/`

#### 2. Routes API

Route `/api/query-table/`

- **Méthode HTTP** : `GET`
- **Description** : Cette route permet d'exécuter une requête SQL sur Athena.
- **Paramètres** :
    - `table` (obligatoire) : Le nom de la table à interroger.
    - `limit` (optionnel) : Le nombre de résultats à retourner.
    - `filter` (optionnel) : La condition de filtre pour la requête.
- **Exemple de requête** :
    
    `GET /api/query-table/?table=kafka_ing_social_data&limit=10&filter=column_name='value'`
    
- **Réponse** :
    - Succès : Les résultats de la requête sous forme JSON.
    - Erreur : Un message d'erreur et le code HTTP 500.

#### 3. Dépendances

Pour utiliser cette API, les bibliothèques suivantes doivent être installées :

- Django : `pip install django`
- Django REST Framework : `pip install djangorestframework`
- drf-yasg : `pip install drf-yasg`
- Boto3 : `pip install boto3`

---

#### 4. Déploiement

Pour lancer l'API :

1. Configurer les permissions IAM pour que l'utilisateur ou le rôle accède à Athena et aux buckets S3.
2. Lancer le serveur Django :
    
    `python manage.py runserver`
    
3. L'API sera accessible à l'adresse `http://127.0.0.1:8000/api/`

Exempke de requete sur Postman :
http://127.0.0.1:8000/api/query-table/?table=kafka_ing_social_data&limit=10
---

#### Conclusion

Avec cette méthodologie, cela :

- Simplifie l'accès aux données Athena.
- Fournit une interface standard pour exécuter des requêtes SQL.
- Compatible avec plusieurs sources de données S3 via Athena.

### 2. Documentation des Endpoints

### Endpoint : `/api/query-table/`

#### **Méthode :**

`GET`

#### **Description :**

Cet endpoint permet d'exécuter une requête SQL sur Athena. Les résultats de la requête sont retournés sous forme de JSON.

#### **Paramètres :**

- `table` (obligatoire) : Le nom de la table à interroger.
- `limit` (optionnel) : Le nombre de résultats à retourner.
- `filter` (optionnel) : La condition de filtre pour la requête.

#### **Exemple d’appel :**

`GET /api/query-table/?table=kafka_ing_social_data&limit=10&filter=column_name='value'`

#### **Exemple de Réponse :**

- **En cas de succès :**
    
    `{     "ResultSet": {         "Rows": [             {                 "Data": [                     {                         "VarCharValue": "value1"                     },                     {                         "VarCharValue": "value2"                     },                     ...                 ]             },             ...         ]     } }`
    
- **En cas d’erreur :**
    
    `{     "error": "Query failed" }`
    

---

### Fonctionnement détaillé

1. **Paramètre obligatoire :**
    
    - Le nom de la table doit être correctement spécifié et correspondre aux tables disponibles dans Athena.
2. **Paramètres optionnels :**
    
    - Si le nombre de résultats (`limit`) n’est pas précisé, une valeur par défaut de 10 est utilisée.
    - Si la condition de filtre (`filter`) n’est pas précisée, aucun filtre ne sera appliqué.
3. **Résultats :**
    
    - Les données sont récupérées directement depuis le data lake S3 via Athena et formatées en JSON pour l'utilisateur.
4. **Erreurs gérées :**
    
    - Problèmes de syntaxe dans la requête SQL.
    - Permissions manquantes pour accéder à Athena ou aux buckets S3.
    - Timeout dans l'exécution de la requête.
