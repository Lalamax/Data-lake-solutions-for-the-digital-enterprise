
from flask import Flask, jsonify, request
import boto3
import time


app = Flask(__name__)

# connexion Athena via boto3
athena_client = boto3.client('athena', region_name='eu-west-3')  


DATABASE = 'DATABASE'  
OUTPUT_BUCKET = 's3://kafka-ing-transactions/'  
LOGS_BUCKET = 's3://kafka-ing-logs/'
SOCIAL_DATA_BUCKET = 's3://kafka-ing-social-data/'
AD_CAMPAIGNS_BUCKET = 's3://kafka-ing-ad-campaigns/'

# Fonction pour exécuter une requête Athena
def execute_athena_query(query, output_bucket=OUTPUT_BUCKET):
    try:
        # Exécution de la requête Athena
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': DATABASE},
            ResultConfiguration={'OutputLocation': output_bucket}
        )

        # Récupération de l'ID de la requête
        query_execution_id = response['QueryExecutionId']

        # Attente que la requête soit terminée
        status = 'RUNNING'
        while status == 'RUNNING':
            result = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = result['QueryExecution']['Status']['State']
            time.sleep(1)

        # Si la requête a réussi, récupération des résultats
        if status == 'SUCCEEDED':
            result = athena_client.get_query_results(QueryExecutionId=query_execution_id)
            return result['ResultSet']['Rows']
        else:
            return {'error': 'La requête a échoué'}

    except Exception as e:
        return {'error': str(e)}


@app.route('/execute_query', methods=['GET'])
def execute_query():
    query = request.args.get('query')
    output_bucket = request.args.get('bucket', OUTPUT_BUCKET)  

 
    if not query:
        return jsonify({"error": "Aucune requête fournie"}), 400


    results = execute_athena_query(query, output_bucket)
    
  
    if 'error' in results:
        return jsonify(results), 500

  
    formatted_results = []
    for row in results:
        formatted_results.append([col['VarCharValue'] for col in row['Data']])

    return jsonify(formatted_results), 200

if __name__ == '__main__':
    app.run(debug=True)
