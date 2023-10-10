from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import receipt_vision

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'  # Thư mục lưu trữ ảnh tải lên
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/sorimachivn-ocr', methods=['POST'])
def call_function():
    try:
        file = request.files['file']
        # Gọi hàm từ tệp .py
        if file:
        # Lưu tệp ảnh vào máy chủ và lấy đường dẫn tệp ảnh
        # Lưu tệp tạm thời vào thư mục đã định nghĩa
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            result = receipt_vision.getResult(file_path)  # Thay "your_function" bằng tên hàm bạn muốn gọi
        # Trả về kết quả
        # return jsonify({'result': result})
        return result

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Xử lý tệp đã chọn
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
