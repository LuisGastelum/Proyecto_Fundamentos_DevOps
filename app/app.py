import boto3
import os
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuración de Clientes AWS
# AWS Academy suele usar us-east-1 por defecto
REGION = 'us-east-1'

ec2_client = boto3.client('ec2', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
cloudwatch = boto3.client('cloudwatch', region_name=REGION)

# --- CONFIGURACIÓN DE RECURSOS ---
AMI_ID = 'ami-098e39bafa7e7303d' 
BUCKET_NAME = 'mi-primer-bucket-030590967045-us-east-1-an' 
TABLA_DYNAMO = 'RegistroActividad'

def enviar_metrica(nombre_metrica):
    """Envia un dato a CloudWatch para el Dashboard"""
    cloudwatch.put_metric_data(
        Namespace='CloudOps_App',
        MetricData=[{
            'MetricName': nombre_metrica,
            'Value': 1,
            'Unit': 'Count'
        }]
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lanzar_ec2')
def lanzar_ec2():
    try:
        instance = ec2_client.run_instances(
            ImageId=AMI_ID,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Instancia-Desde-App'}]}]
        )
        instance_id = instance['Instances'][0]['InstanceId']
        
        enviar_metrica('InstanciasCreadas')
        return jsonify({"mensaje": f"Instancia {instance_id} creada exitosamente"})
    except Exception as e:
        return jsonify({"mensaje": f"Error EC2: {str(e)}"}), 500

@app.route('/respaldar_s3')
def respaldar_s3():
    try:
        file_path = "/tmp/log_backup.txt"
        with open(file_path, "w") as f:
            f.write(f"Respaldo de logs generado el {datetime.now()}")
        
        s3_client.upload_file(file_path, BUCKET_NAME, "log_backup.txt")
        
        enviar_metrica('RespaldosS3')
        return jsonify({"mensaje": "Respaldo subido a S3 correctamente"})
    except Exception as e:
        return jsonify({"mensaje": f"Error S3: {str(e)}"}), 500

@app.route('/registrar_log')
def registrar_log():
    try:
        tabla = dynamodb.Table(TABLA_DYNAMO)
        timestamp = str(datetime.now().timestamp())
        
        tabla.put_item(Item={
            'id': timestamp,
            'evento': 'Acceso al Dashboard',
            'fecha': str(datetime.now()),
            'usuario': 'Admin_CloudOps'
        })
        
        enviar_metrica('RegistrosDynamo')
        return jsonify({"mensaje": "Actividad registrada en DynamoDB"})
    except Exception as e:
        return jsonify({"mensaje": f"Error DynamoDB: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)