from flask import Flask, jsonify, render_template
import boto3
import os

app = Flask(__name__)

# Configuración de clientes de AWS
ec2 = boto3.client('ec2', region_name='us-east-1d')
s3 = boto3.client('s3', region_name='us-east-1')

@app.route("/")
def home():
    # Esta ruta sirve la página web (el HTML)
    return render_template("index.html")

@app.route("/crear-ec2", methods=["POST"])
def crear_instancia():
    try:
        # Lógica para lanzar una instancia nueva
        instance = ec2.run_instances(
            ImageId='ami-098e39bafa7e7303d', # AMI de Amazon Linux
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1
        )
        id_instancia = instance['Instances'][0]['InstanceId']
        return jsonify({"status": "success", "message": f"Instancia {id_instancia} creada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/backup-s3", methods=["POST"])
def backup_s3():
    try:
        # Aquí simulamos subir un archivo de configuración al bucket
        bucket_name = "tu-nombre-de-bucket-unico" # Debe existir en tu cuenta
        file_name = "config_backup.txt"
        
        # Crear un archivo temporal para subir
        with open(file_name, "w") as f:
            f.write("Respaldo de configuracion de la app")
            
        s3.upload_file(file_name, bucket_name, file_name)
        return jsonify({"status": "success", "message": f"Respaldo subido a {bucket_name}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)