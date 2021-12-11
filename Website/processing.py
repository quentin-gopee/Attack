# Import libraries
import numpy as np
from librosa import power_to_db, feature, to_mono, get_duration
from sklearn.manifold import TSNE
from json import dumps
from math import exp
from sklearn.decomposition import PCA
import io
import soundfile as sf


ALLOWED_EXTENSIONS = set(['wav', 'mp3', 'm4a', 'flac', 'aac', 'wma', 'aif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_features(y, sr):
    """Crée un vecteur représentant le son y"""
    if len(y) < sr:
        lack = sr-len(y)
        end = np.zeros(lack)
        y = np.concatenate((y, end))
    y = y[0:sr]  # analyze just first second
    S = feature.melspectrogram(y, sr=sr, n_mels=128)
    log_S = power_to_db(S, ref=np.max)

    mfcc = feature.mfcc(S=log_S, n_mfcc=13)
    delta_mfcc = feature.delta(mfcc)
    delta2_mfcc = feature.delta(mfcc, order=2)

    feature_vector = np.concatenate(
        (np.mean(mfcc, 1), np.mean(delta_mfcc, 1), np.mean(delta2_mfcc, 1)))
    feature_vector = (feature_vector-np.mean(feature_vector)) / \
        np.std(feature_vector)

    return feature_vector


def mfcc_files(files):
    """Retourne la liste des vecteurs pour chaque sons dans la liste files ainsi que la liste de leurs paths"""

    feature_vectors = []
    out_files = []
    i = 0
    j = 0

    for file in files:
        if file and allowed_file(file.filename):
            i += 1
            print("get %d of %d = %s\n" % (i, len(files), file.filename))
            try:
                tmp = io.BytesIO(file.read())
                y, sr = sf.read(tmp)
                y = y.T
                y = to_mono(y)
                if len(y) < 2:
                    print("error loading %s" % file.filename)
                    continue
                feat = get_features(y, sr)
                if np.isnan(np.sum(feat)):
                    print("error loading %s" % file.filename)
                    continue
                feature_vectors.append(feat)
                out_files.append(j)
            except:
                print("error loading %s" % file.filename)
        j += 1

    print("calculated %d feature vectors\n" % len(feature_vectors))

    return feature_vectors, out_files


def vector_colors(feature_vectors):
    """Assigne une couleur à chaque son représenté dans feature_vectors"""

    pca = PCA(n_components=3)
    pca_result = pca.fit_transform(feature_vectors)

    colors = []

    for result in pca_result:

        r_exp = exp(result[2])
        g_exp = exp(result[1])
        b_exp = exp(result[0])

        max_rgb = max(r_exp, g_exp, b_exp)

        r = int(255*r_exp/max_rgb)
        g = int(255*g_exp/max_rgb)
        b = int(255*b_exp/max_rgb)

        color = [r, g, b]
        colors.append(color)

    return colors


def create_map(out_files, feature_vectors, colors):
    """Crée un fichier JSON map_name.json contentant les coordonnées et la couleur de chaque son représenté par feature_vectors dans la map"""

    model = TSNE(n_components=2, learning_rate=150, perplexity=30,
                 verbose=2, angle=0.1).fit_transform(feature_vectors)

    x_axis = model[:, 0]
    y_axis = model[:, 1]

    x_norm = (x_axis - np.min(x_axis)) / (np.max(x_axis) - np.min(x_axis))
    y_norm = (y_axis - np.min(y_axis)) / (np.max(y_axis) - np.min(y_axis))

    data = [{"file": f, "point": [x, y], "color": c} for f, x, y, c in zip(
        out_files, x_norm.astype(float), y_norm.astype(float), colors)]

    data = dumps(data)

    return data
