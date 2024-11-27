from django.http import JsonResponse
import boto3
import time
import logging
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Wil ça c'est le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = boto3.client('athena')
database = 'data-from-kafka'
output_location = 's3://kafka-ing-transactions/athena-results/'

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('table', openapi.IN_QUERY, description="Table name", type=openapi.TYPE_STRING),
        openapi.Parameter('limit', openapi.IN_QUERY, description="Limit number of results", type=openapi.TYPE_INTEGER),
        openapi.Parameter('filter', openapi.IN_QUERY, description="Filter condition", type=openapi.TYPE_STRING)
    ],
    responses={200: 'Success', 500: 'Query failed'}
)
@api_view(['GET'])
def query_table(request):
    table = request.query_params.get('table')
    limit = request.query_params.get('limit', 10)
    filter_condition = request.query_params.get('filter', '')

    if not table:
        return JsonResponse({'error': 'Table name is required'}, status=400)

    query = f"SELECT * FROM {table}"
    if filter_condition:
        query += f" WHERE {filter_condition}"
    query += f" LIMIT {limit}"

    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database
        },
        ResultConfiguration={
            'OutputLocation': output_location
        }
    )

    logger.debug(f"Query Execution ID: {response['QueryExecutionId']}")

    query_execution_id = response['QueryExecutionId']
    while True:
        query_status = client.get_query_execution(QueryExecutionId=query_execution_id)
        state = query_status['QueryExecution']['Status']['State']
        logger.debug(f"Query State: {state}")
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)

    if state == 'SUCCEEDED':
        result = client.get_query_results(QueryExecutionId=query_execution_id)
        return JsonResponse(result, safe=False)
    else:
        error_message = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
        logger.error(f"Query failed: {error_message}")
        return JsonResponse({'error': error_message}, status=500)
