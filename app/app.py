import boto3
import re
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)

# CONFIGURACIÓN DE RECURSOS 
REGION = 'us-east-1'
AMI_ID = 'ami-098e39bafa7e7303d' # Amazon Linux 2023
BUCKET_NAME = 'mi-primer-bucket-030590967045-us-east-1-an' 
TABLA_DYNAMO = 'RegistroActividad' 

# Inicialización de Clientes AWS
ec2 = boto3.client('ec2', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
dynamo = boto3.resource('dynamodb', region_name=REGION)
cw = boto3.client('cloudwatch', region_name=REGION)

def enviar_metrica(nombre_metrica):
    """
    Función auxiliar para enviar métricas personalizadas a CloudWatch.
    Esto es lo que permite que las alarmas tengan datos para evaluar.
    """
    try:
        cw.put_metric_data(
            Namespace='CloudOps_App',
            MetricData=[{
                'MetricName': nombre_metrica,
                'Value': 1,
                'Unit': 'Count'
            }]
        )
    except Exception as e:
        print(f"Error al enviar métrica: {e}")

# RUTAS DE LA APLICACIÓN
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lanzar_ec2')
def lanzar_ec2():
    try:
        # Lanza instancia t2.micro
        res = ec2.run_instances(
            ImageId=AMI_ID, 
            InstanceType='t2.micro', 
            MinCount=1, 
            MaxCount=1
        )
        instance_id = res['Instances'][0]['InstanceId']
        
        # Disparamos la métrica para la Alarma de EC2
        enviar_metrica('InstanciasCreadas')
        
        return jsonify({"mensaje": f"Instancia {instance_id} lanzada con éxito."})
    except Exception as e:
        return jsonify({"mensaje": f"Error EC2: {str(e)}"}), 500

@app.route('/respaldar_s3')
def respaldar_s3():
    try:
        # Creamos un archivo temporal local
        temp_file = "/tmp/log_operaciones.txt"
        with open(temp_file, "w") as f:
            f.write(f"Reporte de sistema generado el {datetime.now()}")
        
        # Subida a S3
        s3.upload_file(temp_file, BUCKET_NAME, "backup_dashboard.txt")
        
        # Disparamos métrica para la Alarma de S3
        enviar_metrica('Uso_S3')
        
        return jsonify({"mensaje": "Archivo de diagnóstico subido a S3."})
    except Exception as e:
        return jsonify({"mensaje": f"Error S3: {str(e)}"}), 500

@app.route('/registrar_log')
def registrar_log():
    try:
        tabla = dynamo.Table(TABLA_DYNAMO)
        # Insertamos un registro con timestamp como ID
        tabla.put_item(Item={
            'id': str(datetime.now().timestamp()),
            'evento': 'Dashboard Action',
            'detalles': 'El usuario ejecutó un log manual',
            'fecha': str(datetime.now())
        })
        
        # Disparamos métrica para la Alarma de Dynamo
        enviar_metrica('Uso_Dynamo')
        
        return jsonify({"mensaje": "Evento auditado en la tabla DynamoDB."})
    except Exception as e:
        return jsonify({"mensaje": f"Error DynamoDB: {str(e)}"}), 500

@app.route('/consultar_alarma/<nombre_alarma>')
def consultar_alarma(nombre_alarma):
    """
    Ruta dinámica que recibe el nombre de la alarma desde el HTML.
    Limpia la respuesta de AWS para que se vea bien en la consola web.
    """
    try:
        res = cw.describe_alarms(AlarmNames=[nombre_alarma])
        
        if res['MetricAlarms']:
            alarma = res['MetricAlarms'][0]
            estado = alarma['StateValue']
            razon_cruda = alarma['StateReason']
            
            # Usamos Regex para extraer solo la parte importante del mensaje
            # Ejemplo: "Threshold Crossed: 1 datapoint was greater than..."
            match = re.search(r'Threshold Crossed:.*?\)', razon_cruda)
            razon_limpia = match.group(0) if match else razon_cruda[:100] + "..."
            
            return jsonify({
                "estado": estado, 
                "razon": razon_limpia
            })
            
        return jsonify({
            "estado": "INEXISTENTE", 
            "razon": f"No se encontró la alarma '{nombre_alarma}' en us-east-1."
        })
        
    except Exception as e:
        return jsonify({"mensaje": f"Error de conexión: {str(e)}"}), 500

# Lanzamiento del servidor
if __name__ == '__main__':
    # Usamos host 0.0.0.0 para que sea accesible desde la IP pública de tu EC2
    app.run(host='0.0.0.0', port=5000, debug=True)