import numpy as np
import torch
from torchvision.utils import draw_bounding_boxes
import torchvision
from torchvision.io import read_image
from tqdm import tqdm_notebook
from PIL import Image, ImageDraw, ImageOps 

class LocalizationModel:
    def __init__(self, 
                 classes, 
                 conf=0.25, 
                 iou=0.45, 
                 agnostic=False, 
                 multi_label=False, 
                 max_det=1000, 
                 amp=False):
        
        # Load the YOLOv5 model
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

        # Set the model's attributes
        self.model.conf = conf
        self.model.iou = iou
        self.model.agnostic = agnostic
        self.model.multi_label = multi_label
        self.model.classes = classes
        self.model.max_det = max_det
        self.model.amp = amp
        
    def localize(self, img_array_list):
        cropped_images = []
        for img_arr in tqdm_notebook(img_array_list):
            pil_img = Image.fromarray(img_arr)
            result = self.model(img_arr)

            for coord in result.xyxy[0]:
                xmin, ymin, xmax, ymax = np.asarray(coord[:4])
                tupled = tuple([xmin, ymin, xmax, ymax])
                cropped = pil_img.crop(tupled)
                cropped_images.append(np.asarray(cropped))

        return cropped_images