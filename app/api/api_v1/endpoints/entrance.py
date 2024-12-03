# pylint: disable=E0401,R0914
"""
    Saves data of the entrance and exit of the employee
"""
from datetime import datetime
from fastapi import APIRouter
from boto3.dynamodb.conditions import Key
from app.classes.adapters.database_dynamo_aws import DatabaseDynamoAWS
from app.classes.adapters.config_aws import ConfigAWS


router = APIRouter()


def has_results(results):
    """
    Check if the results are not empty
    Args:
        results (dict): Results of the query

    Returns:
        bool: True if the results are not empty, False otherwise
    """
    return len(results) > 0


@router.post("/{person}")
def set_entrance(person: str):
    """
        Function that calls the BlinkAPI class to send the 2FA code to the Blink API.

    Args:
        account (Account): all information required for validating a client
        mfa_code (int): this is the sms that you will receive in your phone

    Returns:
        dict : This responses a json with the status_code,
        the response of the server(blank if has no json format) and if is_success
    """

    config_instance = ConfigAWS()
    database_instance = DatabaseDynamoAWS(config_instance)
    now = datetime.now()
    day = now.strftime("%Y%m%d")
    hour = now.strftime("%H:%M:%S")

    query = Key('day').eq(day) & Key('person').eq(person)
    result = database_instance.query(query)
    print(result)
    items = result['response']['Items']
    if has_results(items):
        str_entrada = items[0]['entrada']
        entrada = datetime.strptime(str_entrada, "%H:%M:%S")
        salida = datetime.strptime(hour, "%H:%M:%S")
        key = {"day":  day, "person": person}
        diference = salida - entrada
        seconds = int(diference.total_seconds())
        update_expresion = "SET salida = :salida, working_seconds = :working_seconds"
        expression_attribute_values = {
            ":salida": hour, ":working_seconds": seconds}  # Nuevo valor para Edad
        result = database_instance.update_item(
            key, update_expresion, expression_attribute_values)
        return result
    data = {
        'day': day,  # Clave primaria obligatoria
        'person': person,
        'entrada': hour  # Clave de ordenación obligatoria
    }
    result = database_instance.put_item(data)
    # result = database_instance.query(filter)
    return result
