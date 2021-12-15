from flask import Flask, request, render_template, jsonify
from processing import mfcc_files, vector_colors, create_map

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route("/api", methods=["POST"])
def file_summer_page():
    files = request.files.getlist("files[]")
    print('files : ', files)
    feature_vectors, out_files, full_names = mfcc_files(files)
    colors = vector_colors(feature_vectors)
    sound_map = create_map(out_files, feature_vectors, colors, full_names)
    return jsonify({'sound_map': sound_map})


@app.route("/prod", methods=["GET"])
def webapp():
    return render_template('prod.html')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/info', methods=['GET'])
def info():
    return render_template('info.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
