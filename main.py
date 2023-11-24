# /******************************************************************************
#  All Rights Reserved. Copyright(c) 2023
# *******************************************************************************
#  File Name   : main.py
#  Function    : 
#  Create      : 2023/10/27 V1.0.0.0 ManTrinh
#  Update      :
#  Comment     : 
# ******************************************************************************/

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import receipt_vision
import json
import text_detection
import aipo_test

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
version = r"V1.0.0.3"

@app.route('/sorimachivn-ocr', methods=['POST'])
def call_function():
    try:
        file = request.files['file']
        file_byte_data = file.read()
        result = receipt_vision.getResult(file_byte_data)
        return result

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/sorimachivn-ocr-version', methods=['GET'])
def call_version():
    try:
        ver_json = {}
        ver_json["ver"] = version
        return json.dumps(ver_json, ensure_ascii=False, indent=4)

    except Exception as e:
        return jsonify({'error': str(e)})    
    
@app.route('/sorimachivn-ocr-api', methods=['POST'])
def get_json():
    try:
        file = request.files['file']
        type_ocr = request.args.get('type_ocr', default=None, type=int)
        file_byte_data = file.read()
        result = receipt_vision.getAPI(file_byte_data, type_ocr)
        return result

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/aipo-test', methods=['POST'])
def test():
    try:
        file = request.files['file']
        type_ocr = request.args.get('type_ocr', default=None, type=int)
        file_byte_data = file.read()
        # image_file = os.path.join("./uploads/image/", f.filename)
        # json_file = os.path.join("./uploads/json/", f.filename + ".json")
        # f.save(image_file)
        text_detect = text_detection.GoogleTextDetection()
        text_detect.setup(file_byte_data)
        vline = text_detect.vertical_lines
        lines = []
        for val in vline:
            lines.append(val['text'])
        result = aipo_test.getAPI(lines, type_ocr)
        return result

    except Exception as e:
        return jsonify({'error': str(e)})    

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return f"Tệp '{filename}' đã được tải lên thành công!"

    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=False)
