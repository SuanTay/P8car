from flask import Flask, render_template
from flask_wtf import FlaskForm, validators
from wtforms import  IntegerField
from PIL import Image
import os
import numpy as np
from wtforms.validators import NumberRange
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'

class numForm(FlaskForm):
    num_img = IntegerField("Numéro de l'image entre 0 et 9 :", validators=[NumberRange(min=0, max=9)])

def comput(i):
    # recuperation de l'image suivant un index depuis le Blob d'Azure
    image_dir = os.getenv('path_img')
    image_mask = ""
    image_list = os.listdir(image_dir)
    i = int(i)
    path = f'{image_dir}/{image_list[i]}'
    print('Image path',path)
    name = f'{image_list[i]}'
    #copie l'image dans le dossier static
    imgR = Image.open(path)
    imgR.save(name)
    # image segmentation map
    imgC = myapi(imgR)
    name_c=f'c_{name}'
    imgC.save(name_c)
    #merge
    imgT = merge(imgC, imgR)
    name_t=f't_{name}'
    imgT.save(name_t)
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
    uri = os.getenv('uri')
    key = os.getenv('key')
    input_data = serialize_image(data)
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = f'Bearer {key}'

    response = requests.post(uri,data = input_data, headers=headers)
    print('response OK')
    return deserialize_image(response)

def serialize_image(image):
    import json
    import numpy as np
    import io
    img = np.array(image)
    memfile = io.BytesIO()
    np.save(memfile, img)
    memfile.seek(0)
    data_serialized = json.dumps({'data':memfile.read().decode('latin-1')})
    return(data_serialized)


def deserialize_image(data_serialized):
    import json
    from PIL import Image
    import io
    memfile = io.BytesIO()
    memfile.write(json.loads(data_serialized)['data'].encode('latin-1'))
    memfile.seek(0)

    img = np.load(memfile)
    image = Image.fromarray(img)
    return(image)


@app.route('/form', methods=['GET', 'POST'])
def form():
    form = numForm()

    if form.validate_on_submit():
        path , img_col_path, img_t_path = comput(form.num_img.data)

        return render_template('img.html', img_path=path, img_col = img_col_path, img_t = img_t_path )

    return render_template('form.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
