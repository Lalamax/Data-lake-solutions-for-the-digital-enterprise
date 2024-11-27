from django.http import JsonResponse
import boto3
import time
import logging

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def query_athena(request):
    client = boto3.client('athena')

    # Exemple de requête Athena
    query = "SELECT * FROM your_table LIMIT 10"

    # Démarrez la requête Athena
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': 'data-from-kafka'
        },
        ResultConfiguration={
            'OutputLocation': 's3://kafka-ing-transactions/athena-results/'
        }
    )

    logger.debug(f"Query Execution ID: {response['QueryExecutionId']}")

    # Attendez que la requête soit terminée
    query_execution_id = response['QueryExecutionId']
    while True:
        query_status = client.get_query_execution(QueryExecutionId=query_execution_id)
        state = query_status['QueryExecution']['Status']['State']
        logger.debug(f"Query State: {state}")
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)

    # Récupérez les résultats
    if state == 'SUCCEEDED':
        result = client.get_query_results(QueryExecutionId=query_execution_id)
        return JsonResponse(result, safe=False)
    else:
        error_message = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
        logger.error(f"Query failed: {error_message}")
        return JsonResponse({'error': error_message}, status=500)
