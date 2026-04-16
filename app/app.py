import boto3
import re
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN ---
REGION = 'us-east-1'
AMI_ID = 'ami-098e39bafa7e7303d' 
BUCKET_NAME = 'mi-primer-bucket-030590967045-us-east-1-an'
TABLA_DYNAMO = 'RegistroActividad'
NOMBRE_ALARMA = 'Alarma_Actividad_EC2'

# Clientes AWS
ec2 = boto3.client('ec2', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
dynamo = boto3.resource('dynamodb', region_name=REGION)
cw = boto3.client('cloudwatch', region_name=REGION)

def enviar_metrica(nombre):
    cw.put_metric_data(
        Namespace='CloudOps_App',
        MetricData=[{'MetricName': nombre, 'Value': 1, 'Unit': 'Count'}]
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lanzar_ec2')
def lanzar_ec2():
    try:
        res = ec2.run_instances(ImageId=AMI_ID, InstanceType='t2.micro', MinCount=1, MaxCount=1)
        enviar_metrica('Uso_EC2')
        return jsonify({"mensaje": f"Instancia {res['Instances'][0]['InstanceId']} lanzada."})
    except Exception as e: return jsonify({"mensaje": str(e)}), 500

@app.route('/respaldar_s3')
def respaldar_s3():
    try:
        path = "/tmp/log.txt"
        with open(path, "w") as f: f.write(f"Backup {datetime.now()}")
        s3.upload_file(path, BUCKET_NAME, "backup.txt")
        enviar_metrica('Uso_S3')
        return jsonify({"mensaje": "Respaldo en S3 exitoso."})
    except Exception as e: return jsonify({"mensaje": str(e)}), 500

@app.route('/registrar_log')
def registrar_log():
    try:
        tabla = dynamo.Table(TABLA_DYNAMO)
        tabla.put_item(Item={'id': str(datetime.now().timestamp()), 'evento': 'Log Manual'})
        enviar_metrica('Uso_Dynamo')
        return jsonify({"mensaje": "Registro en DynamoDB guardado."})
    except Exception as e: return jsonify({"mensaje": str(e)}), 500

@app.route('/consultar_alarma')
def consultar_alarma():
    try:
        res = cw.describe_alarms(AlarmNames=[NOMBRE_ALARMA])
        if res['MetricAlarms']:
            alarma = res['MetricAlarms'][0]
            estado = alarma['StateValue']
            razon_cruda = alarma['StateReason']
            
            # FORMATEO DE TEXTO: Limpiamos el JSON y códigos técnicos de AWS
            # Buscamos la frase principal "Threshold Crossed:..."
            match = re.search(r'Threshold Crossed:.*?\)', razon_cruda)
            razon_limpia = match.group(0) if match else razon_cruda[:100] + "..."
            
            return jsonify({"estado": estado, "razon": razon_limpia})
        return jsonify({"estado": "INEXISTENTE", "razon": "No se encontró la alarma."})
    except Exception as e: return jsonify({"mensaje": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)