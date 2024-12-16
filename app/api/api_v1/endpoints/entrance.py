# pylint: disable=E0401,R0914
"""
    Saves data of the entrance and exit of the employee
"""
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from app.classes.adapters.database_dynamo_aws import DatabaseDynamoAWS
from app.classes.adapters.email_aws import EmailAWS
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


@router.get("/{person}/{date_from}/{destination}")
def signing_reporting(person: str, date_from: str, destination: str):
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
    email_instance = EmailAWS(config_instance)
    email_instance.set_destination(destination)
    database_instance = DatabaseDynamoAWS(config_instance)
    query = Key('person').eq(person) & Key('day').gt(date_from)
    result = database_instance.query(query)
    items = result['response']['Items']
    email = '<body><table><tr><th>Fecha</th><th>Entrada</th><th>Salida</th><th>Horas</th></tr>'
    rows = 0
    total_seconds = 0
    media = 0
    for i in items:
        email += '<tr><td>'+i['day']+'</td><td>'+i['entrada']+'</td>'
        if 'salida' in i.keys():
            rows += 1
            working_hours = round(i['working_seconds']/3600, 2)
            total_seconds += i['working_seconds']
            email += '<td>' + i['salida']+'</td><th>' + \
                str(working_hours)+'</td>'
        email += '</tr>'
    if rows > 0:
        total_hours = (total_seconds/3600)/rows
        media = round(total_hours, 2)
        horas = round(total_hours)
        minutos = round(60 * (media - horas))
        media = str(horas) + ' y ' + str(minutos) + " minutos"
    email += '<tr><td></td><td></td><th>Media</th><th>' + \
        str(media)+'</th></tr></table></body>'
    subject = 'Solicitud de horas de ' + person + ' desde ' + date_from
    response = email_instance.send_email(subject, email)
    return response


@router.get("/{person}/{date_from}", response_class=HTMLResponse)
def web_signing_reporting(person: str, date_from: str):
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
    query = Key('person').eq(person) & Key('day').gt(date_from)
    result = database_instance.query(query)
    items = result['response']['Items']
    email = '<body><table><tr><th>Fecha</th><th>Entrada</th><th>Salida</th><th>Horas</th></tr>'
    rows = 0
    total_seconds = 0
    media = 0
    for i in items:
        email += '<tr><td>'+i['day']+'</td><td>'+i['entrada']+'</td>'
        if 'salida' in i.keys():
            rows += 1
            working_hours = round(i['working_seconds']/3600, 2)
            total_seconds += i['working_seconds']
            email += '<td>' + i['salida']+'</td><th>' + \
                str(working_hours)+'</td>'
        email += '</tr>'
    if rows > 0:
        total_hours = (total_seconds/3600)/rows
        media = round(total_hours, 2)
        horas = round(total_hours)
        minutos = round(60 * (media - horas))
        media = str(horas) + ' y ' + str(minutos) + " minutos"
    email += '<tr><td></td><td></td><th>Media</th><th>' + \
        str(media)+'</th></tr></table></body>'
    return HTMLResponse(content=email)
