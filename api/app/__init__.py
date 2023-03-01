import os
import io
from flask import Flask, request, send_from_directory, send_file, after_this_request
from werkzeug.utils import secure_filename
import json
import torch
from torchvision.utils import save_image
from PIL import Image
from .model.net import CDLNet
from .model.utils import img_load
from .model.nle import noise_level

# from flask_cors import CORS

def create_app(test_config=None):
    
    app = Flask(__name__,instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY = 'dev',
        UPLOAD_FOLDER = os.path.join(app.instance_path,'uploads'),
        RESULT_FOLDER = os.path.join(app.instance_path,'results'),
        ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'},
        MAX_CONTENT_LENGTH = 1024 * 1024,
        IMG_NAME = ''
    )

    try:
        os.makedirs(app.instance_path)
        os.mkdir(app.config['UPLOAD_FOLDER'])
        os.mkdir(app.config['RESULT_FOLDER'])
    except OSError:
        pass


    args_file = open(os.path.join('trained_nets/CDLNet_Color/args.json'))
    args = json.load(args_file)
    model = CDLNet(**args['model'],init=False)
    ckpt = torch.load(os.path.join('trained_nets/CDLNet_Color/net.ckpt'), map_location=torch.device('cpu'))
    model.load_state_dict(ckpt['net_state_dict'])
    model.eval()

    def predict(file):
        image = img_load(file)
        if(image.shape[1]==4):
            image = image[:,0:3,:,:]
        sigma = 255 * noise_level(image, method='MAD')
        with torch.no_grad():
            image_p,_ = model(image,sigma)

        return image_p

    def allowed_file(filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/upload', methods=['POST'])
    def upload():
        file = request.files['file']
        filename = secure_filename(file.filename)
        app.config.update(IMG_NAME=filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],app.config['IMG_NAME']))
        
        return ('',204)
    
    @app.route('/process')
    def result():
    
        image_p = predict(os.path.join(app.config['UPLOAD_FOLDER'],app.config['IMG_NAME']))
        save_image(image_p,os.path.join(app.instance_path,app.config['RESULT_FOLDER'],'p_'+app.config['IMG_NAME']))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'],app.config['IMG_NAME']))        

        return send_from_directory(app.config['RESULT_FOLDER'], 'p_'+app.config['IMG_NAME'])

    @app.route('/delete')
    def delete_image():
        os.remove(os.path.join(app.instance_path,app.config['RESULT_FOLDER'],'p_'+app.config['IMG_NAME']))
        return ('',204)

    return app