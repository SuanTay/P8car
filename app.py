from flask import Flask, render_template
from flask_wtf import FlaskForm, validators
from requests.models import Response
from wtforms import IntegerField
from PIL import Image
import os
import numpy as np
from wtforms.validators import NumberRange
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

class numForm(FlaskForm):
    num_img = IntegerField("Numéro de l'image entre 0 et 99 :", validators=[NumberRange(min=0, max=99)])


def comput(i):
    static_path = os.path.join(APP_ROOT, 'static/')
    print('static_url_path',static_path)
    # recuperation de l'image suivant un index depuis le Blob d'Azure
    image_dir = os.getenv('path_img')
    print('image dir ', image_dir)
    image_list = os.listdir(image_dir)
    i = int(i)
    path = f'{image_dir}/{image_list[i]}'
    print('Image path ', path)
    name = f'{image_list[i]}'
    print('name img ', name)
    # copie l'image dans le dossier static
    imgR = Image.open(path)
    imgR= imgR.resize((512,256))
    print('Path enr', f'{static_path}{name}')
    imgR.save(f'{static_path}{name}')
    print('Saved img Original')
    # image segmentation map
    imgC = myapi(imgR)
    name_c = f'c_{name}'
    print('name color ', name_c)
    imgC.save(static_path + name_c)
    # merge
    imgT = merge(imgC, imgR)
    name_t = f't_{name}'
    print('name total ', name_t)
    imgT.save(static_path + name_t)
    print('Image path original', name)
    print('Image path col', name_c)
    print('Image path total', name_t)

    return name, name_c, name_t


def merge(imgPred, img):
    imgPred = imgPred.resize((512, 256))
    img = img.resize((512, 256))
    imgs = Image.blend(img, imgPred, 0.6)
    return imgs


def myapi(data):
    uri = os.getenv('endpoint')
    key = os.getenv('key')
    input_data = serialize_image(data)
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = f'Bearer {key}'
    response: Response = requests.post(uri, data=input_data, headers=headers)
    print('myapi:1 :response OK')
    img = deserialize_json(response.json())
    img = img.resize(((512, 256)))
    print('myapi:2 img OK')
    return img


def serialize_image(image):
    import json
    import numpy as np
    import io
    img = np.array(image)
    memfile = io.BytesIO()
    np.save(memfile, img)
    memfile.seek(0)
    data_serialized = json.dumps({'data': memfile.read().decode('latin-1')})
    return (data_serialized)


def deserialize_image(data_serialized):
    import json
    from PIL import Image
    import io
    memfile = io.BytesIO()
    memfile.write(json.loads(data_serialized)['data'].encode('latin-1'))
    memfile.seek(0)
    img = np.load(memfile)
    print('deserialize_image shape', img.shape)

    image = Image.fromarray(img)
    return (image)

def deserialize_json(data_serialized):
    import json
    from PIL import Image
    import io
    memfile = io.BytesIO()
    memfile.write(json.loads(data_serialized)['data'].encode('latin-1'))
    memfile.seek(0)
    img = np.load(memfile)
    print('deserialize_image shape', img.shape)

    image = Image.fromarray((img * 255).astype(np.uint8))
    return image



@app.route('/form', methods=['GET', 'POST'])
def form():
    form = numForm()

    if form.validate_on_submit():
        path, img_col_path, img_t_path = comput(form.num_img.data)

        return render_template('img.html', img_path=path, img_col=img_col_path, img_t=img_t_path)

    return render_template('form.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
